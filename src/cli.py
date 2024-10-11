import os, subprocess, yaml, sys
from agents_generator import AgentsGenerator
from auto import AutoGenerator

class PraisonAI:
    def __init__(self,agent_file='agents.yaml', framework='', auto=False, init=False, agent_yaml=None) -> None:
        self.agent_yaml = agent_yaml
        self.config_list=[{
            "model": os.environ.get("OPENAI_MODEL_NAME", 'gpt-4o'),
            'base_url':os.environ.get("OPENAI_API_BASE"),
            "api_key":os.environ.get("OPENAI_API_KEY"),

        }]
        self.agent_file= agent_file
        self.framework = framework
        self.auto = auto
        self.init= init

    def run(self):
        self.main()

    def main(self):
        args= self.parse_args()
        if args is None:
            agents_generator = AgentsGenerator(self.agent_file, self.framework, self.config_list)
            result = agents_generator.generate_crew_and_kickoff()
            return result
        
        if args.deploy:
            from .deploy import CloudDeployer
            deployer = CloudDeployer()
            deployer.run_commands()
            return
        
        if getattr(args, 'chat', False):
            self.create_chainlit_chat_interface()
            return
        
        if getattr(args, 'code', False):
            self.create_chainlit_code_interface()
            return
        

        if getattr(args, 'realtime', False):
            self.create_chainlit_realtime_interface()
            return
        

        if args.agent_file=='train':
            package_root= os.pardir.dirname(os.path.abspath(__file__))
            config_yaml_destination = os.path.join(os.getcwd(), 'config.yaml')

            if not os.path.exists(config_yaml_destination) or args.model or args.dataset:
                config = generate_config(model_name = args.model, hf_model_name= args.hf, ollama_model_name= args.ollama, dataset= [{"name": args.dataset}])
                with open('config', 'w') as f:
                    yaml.dump(config, f, default_flow_style= False, indent =2)

            
            if args.hf:
                config['huggingface_save']= "true"

            if args.ollama:
                config['ollama_save']= "true"
        
            if 'init' in sys.argv:
                from .setup.setup_conda_env import main as setup_conda_main

                setup_conda_main()
                print("All packages are intalled")
                return
            
            try:
                result = subprocess.check_output(['conda', 'env', 'list'])
                if 'praison_env' in result.decode('utf-8'):
                    print("COnda environment found")

            except subprocess.CalledProcessError:
                print('COnda environment not found')
                from .setup.setup_conda_env import main as setup_conda_main

                setup_conda_main()
                print("ALL packs installed")

            train_args = sys.argv[2:]
            train_script_path = os.path.join(package_root, 'train.py')

            env= os.environ.copy()
            env['PYTHONUNBUFFERED']= '1'

            stream_subprocess(["conda", "run" , '--no-capture-output', '--name', 'praison_env', 'python', "-u", train_script_path,'train'])
            return

        invocation_cmd= 'ai'
        
        self.framework= args.framework or self.framework

        if args.agent_file:
            if args.agent_file.startswith('tests.test'):
                print('test')

            else:
                self.agent_file

            
        if args.auto or args.init:
            temp_topic = ' '.join(args.auto) if args.auto else ' '.join(args.init)
            self.topic = temp_topic

        elif self.auto or self.init:
            self.topic = self.auto

        if args.auto or self.auto:
            self.agent_file= 'test.yaml'
            generator = AutoGenerator(topic = self.topic, framework = self.framework, agent_file = self.agent_file)
            self.agent_file= generator.generate()
            agents_generator = AgentsGenerator(self.agent_file, self.framework, self.config_list)
            result= agents_generator.generate_crew_and_kickoff()
            return result


        elif args.init or self.init:
            self.agent_file= 'agents.yaml'
            generator = AutoGenerator(topic = self.topic, framework = self.framework, agent_file = self.agent_file)
            self.agent_file= generator.generate()
            print(f"FILE {self.agent_file} created sucessfully")
            
            return f"FILE {self.agent_file} created sucessfully"


        if args.ui:
            if args.ui =='gradio':
                self.create_gradio_interface()

            elif args.ui =='chainlit':
                self.create_chainlit_interface()

        else:
                agents_generator= AgentsGenerator(self.agent_file, self.framework, self.config_list, agent_yaml = self.agent_yaml)
                result= agents_generator.generate_crew_and_kickoff()
                return result
        

        # TODO: agentgen, autogen


















def stream_subprocess(command,env=None):
    process= subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,text=True, env=env)
    for line in iter(process.stdout.readline,''):
        print(line,end='')
        sys.stdout.flush()

    process.stdout.close()
    return_code= process.wait()

    if return_code != 0:
        raise subprocess.CalledProcessError(return_code, command)
    