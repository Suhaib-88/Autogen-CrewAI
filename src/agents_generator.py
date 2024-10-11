import logging, inspect
import importlib,os
import importlib.util
import yaml
import autogen
from pathlib import Path
from tools.base_tool import BaseTool
from tools.code_docs_search_tool import  code_docs_search_tool
from tools.csv_search_tool import csv_search_tool
from .inc.model import AIModel 
from crewai import Agent, Task, Crew

agentops_exists= False
try:
    import agentops
    agentops_exists= True
except ImportError:
    agentops_exists= False


class AgentsGenerator:
    def __init__(self, agent_file, framework, config_list, log_level=None, agent_callback= None, task_callback= None, agent_yaml= None):
        self.agent_file= agent_file
        self.framework= framework
        self.config_list= config_list
        self.log_level = log_level
        self.agent_callback= agent_callback
        self.task_callback= task_callback
        self.agent_yaml= agent_yaml
        self.log_level= log_level or logging.getLogger().getEffectiveLevel()

        logging.basicConfig(level= self.log_level, format= '%(asctime)s - %(levelname)s - %(message)s')

        self.logger= logging.getLogger(__name__)
        self.logger.setLevel(self.log_level)


    def is_function_or_decorated(self,obj):
        return inspect.isfunction(obj) or hasattr(obj, '__call__')
    
    def load_tools_from_module(self, module_path):
        spec= importlib.util.spec_from_file_location('tools_module', module_path)
        module= importlib.util.module_from_spec(spec)
        return {name: obj for name, obj in inspect.getmembers(module, self.is_function_or_decorated)}
    
    def load_tools_from_module_class(self, module_path):
        spec= importlib.util.spec_from_file_location('tools_module', module_path)
        module= importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return {name: obj() for name, obj in inspect.getmembers(module, lambda x: inspect.isclass(x) and (x.__module__.startswith('langchain_community.tools') or issubclass(x, BaseTool)) and x is not BaseTool)}
    


    def generate_crew_and_kickoff(self):
        if self.agent_yaml:
            config=yaml.safe_load(self.agent_yaml)

        else:
            if self.agent_file =='/app/api:app' or self.agent_file =='api:app':
                self.agent_file='agents.yaml'

            try:
                with open(self.agent_file, 'r') as f:
                    config = yaml.safe_load(f)
            except FileNotFoundError:
                print(f'File not found: {self.agent_file}')
                return            
            
        topic = config['topic']
        tools_dict={
            'CodeDocsSearchTool': CodeDocsSearchTool(),
            'CSVSearchTool': CSVSearchTool(),
            'DirectorySearchTool': DirectorySearchTool(),
            "DOCXSearchTool":DOCXSearchTool(),
            "DirectoryReadTool": DirectoryReadTool(),
            ## todos

        }
        root_directory= os.getcwd()
        tools_py_path = os.path.join(root_directory, 'tools.py')
        tools_dir_path= Path(root_directory)/'tools'

        if os.path.isfile(tools_py_path):
            tools_dict.update(self.load_tools_from_module_class(tools_py_path))
            self.logger.debug('Tools.py exist s in root directory')

        elif tools_dir_path.is_dir():
            tools_dict.update(self.load_tools_from_module_class(tools_dir_path))
            self.logger.debug('Tools folder exists in the root dir')

        
        framework = self.framework or config.get('framework')

        agents= []
        tasks= []

        if framework=='autogen':
            llm_config = {'config_list':self.config_list}

            if agentops_exists:
                agentops.init(os.environ.get("AGENTOPS_API_KEY"), tags= ['autogen'])
            user_proxy = autogen.UserProxyAgent(name='User', human_input_mode= 'NEVER', is_termination_msg= lambda x:(x.get('content') or '').rstrip().rstrip('.')
                                                .lower().endswith('terminate') or "TERMINATE" in (x.get('content') or '')
            ,code_execution_config= {
                "work_dir": "coding",
                "use_docker":False
            })

            for role, details in config['roles'].items():
                agent_name=details['role'].format(topic=topic).replace("{topic}", topic)
                agent_goal= details['goal'].format(topic=topic)

                agents[role]= autogen.AssistantAgent(name= agent_name, llm_config= llm_config, system_message= details['backstory'].format(topic=topic)+". Must Reply \TERMINATE\ in the end when all is done")
        
                for tool in details.get('tools', []):
                    if tool in tools_dict:
                        try:
                            tool_class= globals()[f'autogen_{type(tools_dict[tool]).__name__}']
                            print(f'found {tool_class.__name__} for {tool}')
                        except KeyError:
                            print(f"Warning autogen_{type(tools_dict[tool]).__name__}")
                            continue
                        tool_class(agents[role], user_proxy)

                for task_name, task_details in details.get('tasks',{}).items():
                    description_filled= task_details['description'].format(topic=topic)
                    expected_output_filed= task_details['expected_output'].format(topic=topic)

                    chat_task={
                        'recipient': agents[role],
                        'message': description_filled,
                        "summary_method":"last_msg"
                    }
                    tasks.append(chat_task)

            response= user_proxy.initiate_chats(tasks)
            result= "## Output ### \n "+ response[-1].summary if hasattr(response[-1], "summary") else ""
            if agentops_exists:
                agentops.end_session('Sucess')
        else:
            if agentops_exists:
                agentops.init(os.environ.get("AGENTOPS_API_KEY"),tags=['crewai'])

            tasks_dict= {}

            for role, details in config['roles'].items():
                role_filled= details['role'].format(topic= topic)
                goal_filled= details['goal'].format(topic=topic)
                backstory_filled= details['backstory'].format(topic=topic)

                agent_tools= [tools_dict[tool] for tool in details.get('tools',[]) if tool in tools_dict]
                llm_model= details.get('llm')

                if llm_model:
                    llm= AIModel(model= llm_model.get('model', os.getenv('MODEL_NAME','openai/gpt-4o')),).get_model()

                else:
                    function_calling_llm= AIModel().get_model()

                agent= Agent(role= role_filled, goal= goal_filled,backstory= backstory_filled, tools= agent_tools, allow_delegation = details.get('allow_delegation', False), 
                             llm= llm,system_template=details.get('system_template'), prompt_template= details.get('prompt_template'), response_template= details.get('response_template'))
                
                if self.agent_callback:
                    agent.step_callback= self.agent_callback

                agents[role]= agent

                for task_name, task_details in details.get('tasks', {}).items():
                    description_filled= task_details['description'].format(topic= topic)
                    expected_output_filled= task_details['expected_output'].format(topic= topic)

                    task = Task(
                        description=description_filled,  # Clear, concise statement of what the task entails
                        expected_output=expected_output_filled,  # Detailed description of what task's completion looks like
                        agent=agent,  # The agent responsible for the task
                        tools=task_details.get('tools', []),  # Functions or capabilities the agent can utilize
                        async_execution=task_details.get('async_execution') if task_details.get('async_execution') is not None else False,  # Execute asynchronously if set
                        context=[], ## TODO: 
                        config=task_details.get('config') if task_details.get('config') is not None else {},  # Additional configuration details
                        output_json=task_details.get('output_json') if task_details.get('output_json') is not None else None,  # Outputs a JSON object
                        output_pydantic=task_details.get('output_pydantic') if task_details.get('output_pydantic') is not None else None,  # Outputs a Pydantic model object
                        output_file=task_details.get('output_file') if task_details.get('output_file') is not None else "",  # Saves the task output to a file
                        callback=task_details.get('callback') if task_details.get('callback') is not None else None,  # Python callable executed with the task's output
                        human_input=task_details.get('human_input') if task_details.get('human_input') is not None else False,  # Indicates if the task requires human feedback
                        create_directory=task_details.get('create_directory') if task_details.get('create_directory') is not None else False  # Indicates if a directory needs to be created
                    )

                    if self.task_callback:
                        task.callback= self.task_callback

                    tasks.append(task)
                    tasks_dict[task_name]= task

            
            for role, details in config['roles'].items():
                for task_name, task_details in details.get('tasks', {}).items():
                    task= tasks_dict[task_name]
                    context_tasks= [tasks_dict[ctx] for ctx in task_details.get('context',[]) if ctx in tasks_dict]
                    task.context= context_tasks

            crew= Crew(agents= list(agents.values()), tasks= tasks, verbose=2)
            self.logger.debug('Final Crew Configuration')
            self.logger.debug(f"Agents:{crew.agents}")
            self.logger.debug(f'Tasks:{crew.tasks}')

            response= crew.kickoff()
            result= f"### Task Output ### \n{response}"
            if agentops_exists:
                agentops.end_session('Success')
        return result


