from fabric import Connection
import sys

# Prepare for deployment
c = Connection('localhost')

def test():
    try:
        result = c.run(
            "python test_tasks.py -v && python test_users.py -v", warn=True
        )
        if result.failed:
            user_input = input("Tests failed. Continue? (yes/no): ")
            if user_input.lower() != "yes":
                sys.exit("Aborted at user request.")
    except Exception as e:
        print(f"Test execution error: {e}")
        sys.exit("Aborted due to errors.")

def commit():
    message = input("Enter a git commit message: ")
    c.run(f"git add . && git commit -am '{message}'")

def push():
    result = c.run("git push origin master", warn=True)
    if result.failed:
        sys.exit("Git push failed, aborting deployment.")

def prepare():
    test()
    commit()
    push()

# Deploy to Heroku
def pull():
    result = c.run("git pull origin master", warn=True)
    if result.failed:
        sys.exit("Git pull failed, aborting deployment.")

def heroku():
    result = c.run("git push heroku master", warn=True)
    if result.failed:
        sys.exit("Heroku push failed, aborting deployment.")

def heroku_test():
    result = c.run(
        "heroku run python test_tasks.py -v && heroku run python test_users.py -v", warn=True
    )
    if result.failed:
        sys.exit("Heroku tests failed, aborting deployment.")

def deploy():
    pull()
    test()
    commit()
    heroku()
    heroku_test()

# Rollback
def rollback():
    c.run("heroku rollback")
