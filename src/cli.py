import os, subprocess, yaml, sys
from agents_generator import AgentsGenerator
from auto import AutoGenerator
import gradio as gr

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
        


    def parse_args(self):
        parser= argparse.ArgumentParser(description= "PraisonAI")
        parser.add_argument('--framework', type=str, help= 'Framework to use')
        parser.add_argument('--agent_file', type=str, help= 'Path to the agent file')
        parser.add_argument('--auto', type=str, help= 'Auto generate')
        parser.add_argument('--init', type=str, help= 'Initialize')
        parser.add_argument('--ui', type=str, help= 'UI to use')
        parser.add_argument('--chat', action= 'store_true', help= 'Chat interface')
        parser.add_argument('--code', action= 'store_true', help= 'Code interface')
        parser.add_argument('--realtime', action= 'store_true', help= 'Realtime interface')
        parser.add_argument('--deploy', action= 'store_true', help= 'Deploy')
        args, unknown_args= parser.parse_known_args()


        if unknown_args and unknown_args[0] == '-b' and unknown_args[1] == 'api:app':
            args.agent_file= 'agents.yaml'

        if args.agent_file=='api:app' or args.agent_file=='/app/api:app':
            args.agent_file= 'agents.yaml'

        if args.agent_file== 'ui':
            args.ui = 'chainlit'

        if args.agent_file== 'chat':
            args.ui = 'chainlit'
            args.chat= True

        if args.agent_file== 'code':
            args.ui = 'chainlit'
            args.code= True

        if args.agent_file== 'realtime':
            args.realtime= True

        return args
    

    def create_chainlit_chat_interface(self):
        if CHAINLIT_AVAILABLE:
            import praisonai

            os.environ['CHAINLIT_PORT']= '8084'
            root_path= os.path.join(os.path.dirname(praisonai.__file__), '.praison')
            os.environ['CHAINLIT_ROOT_PATH']= root_path
            public_folder= os.path.join(os.path.dirname(praisonai.__file__), 'public')
            if not os.path.exists(os.path.join(root_path, 'public')):
                if os.path.exists(public_folder):
                    shutil.copytree(public_folder, os.path.join(root_path, 'public'), dirs_exist_ok= True)
                    
                else:
                    logger.warning('No public folder found')
            else:
                logging.info('Chainlit interface already exists')

            chat_ui_path = os.path.join(os.path.dirname(praisonai.__file__), 'ui', 'chat.py')

            chainlit_run([chat_ui_path])

        else:
            print('Chainlit is not available')


    def create_code_interface(self):
        if CHAINLIT_AVAILABLE:
            import praisonai

            os.environ['CHAINLIT_PORT']= '8086'
            root_path= os.path.join(os.path.expanduser("~"), '.praison')
            os.environ['CHAINLIT_ROOT_PATH']= root_path
            public_folder= os.path.join(os.path.dirname(praisonai.__file__), 'public')
            if not os.path.exists(os.path.join(root_path, 'public')):
                if os.path.exists(public_folder):
                    shutil.copytree(public_folder, os.path.join(root_path, 'public'), dirs_exist_ok= True)
                    
                else:
                    logger.warning('No public folder found')
            else:
                logging.info('Chainlit interface already exists')

            code_ui_path = os.path.join(os.path.dirname(praisonai.__file__), 'ui', 'code.py')
            chainlit_run([code_ui_path])

        else:
            print('CODE Ui is not available')


    def create_gradio_interface(self):
        if GRADIO_AVAILABLE:
            def generate_crew_and_kickoff_interface(auto_args, framework):
                self.framework= framework
                self.agent_file= 'test.yaml'
                generator = AutoGenerator(topic = auto_args, framework = framework)
                self.agent_file= generator.generate()
                agents_generator= AgentsGenerator(self.agent_file, self.framework, self.config_list)

                result= agents_generator.generate_crew_and_kickoff()
                return result
            
            gr.Interface(fn= generate_crew_and_kickoff_interface, inputs= [gr.Textbox(lines=2, label='Auto Args'), gr.Dropdown(choices=['crewai', 'autogen'],label='Framework')], outputs= 'text', title= 'PraisonAI', description= 'PraisonAI is a framework for building AI agents').launch(share= True)

        else:
            print('Gradio is not available')


    def create_chainlit_interface(self):
        if CHAINLIT_AVAILABLE:
            import praisonai

            os.environ['CHAINLIT_PORT']= '8082'
            public_folder= os.path.join(os.path.dirname(praisonai.__file__), 'public')
            if not os.path.exists('public'):
                if os.path.exists(public_folder):
                    shutil.copytree(public_folder, os.path.join(root_path, 'public'), dirs_exist_ok= True)
                    
                else:
                    logging.warning('No public folder found')
            else:
                logging.info('Chainlit interface already exists')

            chat_ui_path = os.path.join(os.path.dirname(praisonai.__file__), 'chainlit_ui.py')
            chainlit_run([chat_ui_path])

        else:
            print('Chainlit is not available')
            
            
    def create_realtime_interface(self):
        if CHAINLIT_AVAILABLE:
            import praisonai

            os.environ['CHAINLIT_PORT']= '8088'
            root_path= os.path.join(os.path.expanduser("~"), '.praison')
            os.environ['CHAINLIT_ROOT_PATH']= root_path
            public_folder= os.path.join(os.path.dirname(praisonai.__file__), 'public')
            if not os.path.exists(os.path.join(root_path, 'public')):
                if os.path.exists(public_folder):
                    shutil.copytree(public_folder, os.path.join(root_path, 'public'), dirs_exist_ok= True)
                    
                else:
                    logging.warning('No public folder found')
            else:
                logging.info('Chainlit interface already exists')

            realtime_ui_path = os.path.join(os.path.dirname(praisonai.__file__), 'ui', 'realtime.py')
            chainlit_run([realtime_ui_path])

        else:
            print('Error Realtime interface is not available')
            


if __name__ == '__main__':
    praison_ai= PraisonAI()
    praison_ai.run()











def stream_subprocess(command,env=None):
    process= subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,text=True, env=env)
    for line in iter(process.stdout.readline,''):
        print(line,end='')
        sys.stdout.flush()

    process.stdout.close()
    return_code= process.wait()

    if return_code != 0:
        raise subprocess.CalledProcessError(return_code, command)
    