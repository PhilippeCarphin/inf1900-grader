from os import listdir, path
from subprocess import run, PIPE, STDOUT
from git import Repo

from asking import get_assignment_short_name, get_grader_name, get_group_number, get_grading_directory, \
    get_assignment_deadline, get_assignment_subdirectories, get_sample_grading_file

root_directory = path.dirname(path.realpath(__file__))
bad_files_list = f"{root_directory}/samples/bad-files.gitignore"


def get_teams_list(grading_directory: str):
    return [team for team in listdir(grading_directory) if path.isdir(path.join(grading_directory, team))]


def generate_partial_grading_file(assignment_name: str, group: str, grader_name: str, sample_grading_file: str):
    with open(sample_grading_file, 'r') as f:
        raw_grading_file_content = f.read()

    partial_grading_file_content = raw_grading_file_content \
        .replace("__TRAVAIL_PRATIQUE__", assignment_name) \
        .replace("__SECTION__", group) \
        .replace("__CORRECTEUR__", grader_name)

    return partial_grading_file_content


def create_branch(repo_path: str, deadline: str, grading_name: str):
    repo = Repo(repo_path)
    deadline_commit = repo.git.rev_list("-n 1", f'--before="{deadline}"', "master")
    return repo.create_head(grading_name, deadline_commit)


def get_commit_info(repo_path: str):
    header = "\n\n======================= Basé sur le commit suivant ============================="
    commit_info = Repo(repo_path).git.log("-1")
    return f"{header}\n{commit_info}"


def get_useless_files(repo_path: str):
    header = "\n\n====================== Fichiers Indésirables ==================================="
    useless_file_list = Repo(repo_path).git.ls_files("-i", f"--exclude-from={bad_files_list}")
    return f"{header}\n{useless_file_list}"


def get_make_output(repo_path: str, subdirectories: list):
    header = "\n\n====================== Output de make pour les problemes ======================="

    make_output = ""
    for subdirectory in subdirectories:
        make_output += "============== output de make dans " + subdirectory + " ============================"
        result = run(["make", "-C", f"{repo_path}/{subdirectory}"], stdout=PIPE, stderr=STDOUT)
        make_output += "\n" + result.stdout.decode('utf-8') + "\n"

    return f"{header}\n{make_output}"


def generate_grading_name(assignment_name: str):
    return f"Correction_{assignment_name}"


def generate_grading_file_name(assignment_name: str):
    return f"{generate_grading_name(assignment_name)}.txt"


def grade(grading_directory: str, group: str):
    grader_name = get_grader_name()
    assignment_name = get_assignment_short_name()
    sample_grading_file = get_sample_grading_file()

    if group is None:
        group = get_group_number()

    if grading_directory is None:
        grading_directory = get_grading_directory()

    deadline = get_assignment_deadline()
    subdirectories = get_assignment_subdirectories()

    partial_grading_text = generate_partial_grading_file(assignment_name, group, grader_name, sample_grading_file)

    teams = get_teams_list(grading_directory)
    for team in teams:
        print(f"Grading team {team}...")

        repo_path = f"{grading_directory}/{team}"
        create_branch(repo_path, deadline, generate_grading_name(assignment_name)).checkout()

        grading_text = partial_grading_text.replace("__TEAM_NUMBER__", team)
        grading_text += get_commit_info(repo_path)
        grading_text += get_useless_files(repo_path)
        grading_text += get_make_output(repo_path, subdirectories)

        grade_file_path = f"{repo_path}/{generate_grading_file_name(assignment_name)}"
        with open(grade_file_path, 'w') as f:
            f.write(grading_text)

    return grading_directory, group, assignment_name
