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

from jwt import JWT, jwk_from_pem
import time
import sys


def get_git_root():
    """Try and guess the git repo, since the conf.yml can be at the repo root"""
    try:
        repo = git.Repo(search_parent_directories=True)
        return repo.working_tree_dir
    except git.InvalidGitRepositoryError:
        return None

def get_github_token():

	# TODO Get the App ID using SUPABASE -> in the payload find user.login to match to supabase userLogin
	if len(sys.argv) > 2:
			app_id = sys.argv[2]
	else:
			app_id = input("Enter your APP ID: ")

	# TODO from local config/env
	with open('privateKey.pem') as pem_file:
			signing_key = jwk_from_pem(pem_file.read())

	payload = {
			'iat': int(time.time()),
			'exp': int(time.time()) + 600,
			'iss': app_id
	}

	jwt_instance = JWT()
	encoded_jwt = jwt_instance.encode(payload, signing_key, alg='RS256')

	return encoded_jwt


def main(req):
  # TODO if action.added or action.created from req, add to supabase
  
  # TODO parse from req to get payload. req.body.payload
  # TODO if payload.action.labeled === genpr then run the code below
  
  token = get_github_token()

	# TODO clone git repo in folder /tmp
	# TODO In future find out how to just remote access git repo
  
  # TODO set git root to /tmp
  git_root = get_git_root()
  
  
  # TODO parse message(text in issue) from payload
  message = ''
  
  
  conf_fname = Path(".aider.conf.yml")

  default_config_files = [conf_fname.resolve()]  # CWD
  if git_root:
      git_conf = Path(git_root) / conf_fname  # git root
      if git_conf not in default_config_files:
          default_config_files.append(git_conf)
  default_config_files.append(Path.home() / conf_fname)  # homedir
  default_config_files = list(map(str, default_config_files))

  
  
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
  
  # TODO properly replace, commit, and push these changes as a pr using github api
        
@app.get("/test/{message}")
async def root(req: str = None):
  try:
    main(req)
  except Exception as e: 
    return {"message": f'Error {e}'}
  return {"message": "Hello World"}