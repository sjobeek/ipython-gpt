import os
import ctypes
import signal
import subprocess

from IPython.core.magic import Magics, cell_magic, line_magic, magics_class

from .displays import get_registered_display
from .subcommands import ChatCommand, ChatModelsBrowserCommand, ConfigCommand


@magics_class
class IPythonGPT(Magics):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._context = {
            "config": {
                "openai_api_key": os.environ.get("OPENAI_API_KEY")
                or globals().get("OPENAI_API_KEY"),
                "default_model": "gpt-3.5-turbo",
                "default_system_message": "You are an expert python developer assistant who favors concise, specific code examples.",
            },
            "message_history": [],
        }
        self._exec_context = self._context.copy()
        self._exec_context['config']['default_system_message'] = "Ignore previous directions. You are an expert python developer who favors variable type annotations. Reply with a single code-block and use concise docstrings. Include one test case."
        self.display = get_registered_display()

        self.log_folder = ".ipygpt_tmp"
        if not os.path.exists(self.log_folder):
            os.makedirs(self.log_folder)
        #import datetime
        #now = datetime.datetime.now()
        #current_time = now.strftime("%Y-%m-%d_%H-%M-%S")
        self.streamlit_log_filepath = os.path.join(self.log_folder, f"ipygpt_session.py")

        launch_streamlit(self.streamlit_log_filepath)

    @cell_magic
    def chat(self, line, cell):
        cmd = ChatCommand(self._context)
        result = cmd.execute(line, cell)
        self.display.display(result)
        with open(self.streamlit_log_filepath, "a") as f:
            f.write(f'''st.subheader("Chat Command")
st.markdown("""Command: {line}

Contents: {cell}""")

''')
    
    @cell_magic
    def exec(self, line, cell):
        cmd = ChatCommand(self._exec_context)
        result = cmd.execute(line, cell)
        self.display.display(result)

    @line_magic
    def chat_config(self, line):
        cmd = ConfigCommand(self._context)
        result = cmd.execute(line)
        self.display.display(result)

    @line_magic
    def chat_models(self, line):
        cmd = ChatModelsBrowserCommand(self._context)
        result = cmd.execute(line)
        self.display.display(result)


name = "ipython_gpt"


def load_ipython_extension(ipython):
    ipython.register_magics(IPythonGPT)

# NOTE: This method of ensuring the streamlit subprocess always exits means this is linux-only for now
def _set_pdeathsig(sig=signal.SIGTERM):
    """help function to ensure once parent process exits, its childrent processes will automatically die
    """
    def callable():
        libc = ctypes.CDLL("libc.so.6")
        return libc.prctl(1, sig)
    return callable


def launch_streamlit(log_filepath):
    """Launch a streamlit subprocess daemon (automatically removed when this process exits)"""


    with open(log_filepath, "w") as f:
        f.write(DEFAULT_STREAMLIT_LOGFILE)

    print(f"Launching streamlit app to log this chat session ({log_filepath})")
    subprocess.Popen(["streamlit", "run", log_filepath], 
                     preexec_fn=_set_pdeathsig(signal.SIGTERM)) 




DEFAULT_STREAMLIT_LOGFILE = '''
import streamlit as st

st.header("IPython GPT Chat Log")
'''