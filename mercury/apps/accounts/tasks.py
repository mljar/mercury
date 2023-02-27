from celery import shared_task


@shared_task(bind=True)
def task_send_invitation(self, job_params):
    print("TODO: send invitation")
    print(job_params["db_id"])
