from celery import shared_task

@shared_task(bind=True)
def task_send_invitation(self, job_params):
    print("send invitation")
    print(job_params["db_id"])
    