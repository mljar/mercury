import logging

log = logging.getLogger(__name__)


def get_running_machines():
    return []


def shuffle_machines(machines):
    return []


def list_instances():
    pass


def start_new_instance(worker_id):
    pass


def start_sleeping_instance(instance_id):
    pass


def terminate_instance(instance_id):
    pass


def hibernate_instance(instance_id):
    pass


def need_instance(worker_id):
    pass


def scale_down():
    log.info("Scale instances down")
