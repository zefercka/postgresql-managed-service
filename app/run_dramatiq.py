import os

from dramatiq.cli import main as dramatiq_main

if __name__ == "__main__":
    os.environ["DB_DRIVER"] = "postgresql+psycopg2"
    os.environ["REPOSITORY_TYPE"] = "sync"
    os.environ["TF_LOG"] = "DEBUG"

    dramatiq_main()


# python app/run_dramatiq.py app.src.tasks.create_vm_task --queue default --threads 1
