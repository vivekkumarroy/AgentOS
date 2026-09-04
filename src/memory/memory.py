import logging
from ..models.state import AgentState, Plan, Observation, TaskStatus

logger = logging.getLogger(__name__)

class ShortTermMemory:
    def __init__(self):
        self.state = AgentState(user_goal="")

    def set_goal(self, goal: str):
        self.state.user_goal = goal
        logger.debug(f"Goal set in memory: {goal}")

    def set_plan(self, plan: Plan):
        self.state.current_plan = plan
        # Initialize tasks_state map
        self.state.tasks_state = {task.task_id: task for task in plan.tasks}
        logger.debug("Plan saved to memory.")

    def add_observation(self, observation: Observation):
        self.state.observations.append(observation)
        logger.debug(f"Observation added: {observation.status}")

    def update_task_status(self, task_id: str, status: TaskStatus):
        if task_id in self.state.tasks_state:
            self.state.tasks_state[task_id].status = status
            logger.debug(f"Task {task_id} status updated to {status}")
        else:
            logger.warning(f"Attempted to update status of unknown task: {task_id}")

    def get_state(self) -> AgentState:
        return self.state

    def clear(self):
        self.state = AgentState(user_goal="")
        logger.debug("Memory cleared.")
