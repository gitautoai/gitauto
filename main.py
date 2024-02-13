import argparse
import os
import sys
from pathlib import Path

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, parent_dir)
import configargparse
import git
import openai
from inputoutput import InputOutput
from fastapi import FastAPI
import models
from coders import Coder

app = FastAPI()


def get_git_root():
    """Try and guess the git repo, since the conf.yml can be at the repo root"""
    try:
        repo = git.Repo(search_parent_directories=True)
        return repo.working_tree_dir
    except git.InvalidGitRepositoryError:
        return None


def main(message):
  
  git_root = get_git_root()
  
  conf_fname = Path(".aider.conf.yml")

  default_config_files = [conf_fname.resolve()]  # CWD
  if git_root:
      git_conf = Path(git_root) / conf_fname  # git root
      if git_conf not in default_config_files:
          default_config_files.append(git_conf)
  default_config_files.append(Path.home() / conf_fname)  # homedir
  default_config_files = list(map(str, default_config_files))
  # parser = configargparse.ArgumentParser(
  #     description="aider is GPT powered coding in your terminal",
  #     add_config_file_help=True,
  #     default_config_files=default_config_files,
  #     config_file_parser_class=configargparse.YAMLConfigFileParser,
  #     auto_env_var_prefix="AIDER_",
  # )
  
  
  io = InputOutput(
      pretty=True,
      yes=True,
      input_history_file=None,
      chat_history_file=None,
      input=input,
      output=None,
      user_input_color="blue",
      tool_output_color=None,
      tool_error_color="red",
      encoding="utf-8",
      dry_run=False,
  ) 
  # fnames = [str(Path(fn).resolve()) for fn in files]
  # if len(args.files) > 1:
  #     good = True
  #     for fname in args.files:
  #         if Path(fname).is_dir():
  #             io.tool_error(f"{fname} is a directory, not provided alone.")
  #             good = False
  #     if not good:
  #         io.tool_error(
  #             "Provide either a single directory of a git repo, or a list of one or more files."
  #         )
  #         return 1

  git_dname = None
  # if len(args.files) == 1:
  #     if Path(args.files[0]).is_dir():
  #         if args.git:
  #             git_dname = str(Path(args.files[0]).resolve())
  #             fnames = []
  #         else:
  #             io.tool_error(f"{args.files[0]} is a directory, but --no-git selected.")
  #             return 1

  io.tool_output(*sys.argv, log_only=True)
  args = None
  # def scrub_sensitive_info(text):
  #     # Replace sensitive information with placeholder
  #     return text.replace(args.openai_api_key, "***")
  # show = scrub_sensitive_info(parser.format_values())
  # io.tool_output(show)
  # io.tool_output("Option settings:")
  # for arg, val in sorted(vars(args).items()):
  #     io.tool_output(f"  - {arg}: {scrub_sensitive_info(str(val))}")

  openai_api_key = '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'


  kwargs = dict()
  client = openai.OpenAI(api_key=openai_api_key, **kwargs)

  main_model = models.Model.create('gpt-4-0613', client)

  try:
      coder = Coder.create(
          main_model=main_model,
          edit_format=None,
          io=io,
          skip_model_availabily_check=False,
          client=client,
          ##
        fnames=None,
        git_dname=None,
        pretty=True,
        show_diffs=False,
        auto_commits=True,
        dirty_commits=True,
        dry_run=False,
        map_tokens=1024,
        verbose=True,
        assistant_output_color="blue",
        code_theme="default",
        stream=True,
        use_git=True,
        voice_language=None,
        aider_ignore_file=None,
      )
  except ValueError as err:
      io.tool_error(str(err))
      return 1


  io.tool_output("Use /help to see in-chat commands, run with --help to see cmd line args")

  if git_root and Path.cwd().resolve() != Path(git_root).resolve():
      io.tool_error(
          "Note: in-chat filenames are always relative to the git working dir, not the current"
          " working dir."
      )

      io.tool_error(f"Cur working dir: {Path.cwd()}")
      io.tool_error(f"Git working dir: {git_root}")


  io.add_to_input_history(message)
  io.tool_output()
  coder.run(with_message=message)
  
        
@app.get("/{message}")
async def root(message: str = None):
  try:
    main(message)
  except Exception as e: 
    return {"message": f'Error {e}'}
  return {"message": "Hello World"}