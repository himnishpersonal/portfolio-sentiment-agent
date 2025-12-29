"""Base agent class with common functionality."""

import logging
import time
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict

from config.logging_config import get_agent_logger


class AgentState(Enum):
    """Agent execution state."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class BaseAgent(ABC):
    """Abstract base class for all agents."""

    def __init__(self, name: str):
        """Initialize base agent.

        Args:
            name: Agent name for logging.
        """
        self.name = name
        self.logger = get_agent_logger(name)
        self.state = AgentState.PENDING
        self.execution_time: float | None = None

    @abstractmethod
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent logic.

        Args:
            input_data: Input data dictionary.

        Returns:
            Output data dictionary.

        Raises:
            Exception: If execution fails.
        """
        pass

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run agent with error handling and timing.

        Args:
            input_data: Input data dictionary.

        Returns:
            Output data dictionary.

        Raises:
            Exception: If execution fails after retries.
        """
        self.state = AgentState.RUNNING
        start_time = time.time()

        try:
            self.logger.info(f"Starting {self.name} execution")
            output_data = self.execute(input_data)
            self.state = AgentState.COMPLETED
            self.execution_time = time.time() - start_time
            self.logger.info(
                f"{self.name} completed successfully in {self.execution_time:.2f} seconds"
            )
            return output_data

        except Exception as e:
            self.state = AgentState.FAILED
            self.execution_time = time.time() - start_time
            self.logger.error(f"{self.name} failed after {self.execution_time:.2f} seconds: {e}", exc_info=True)
            raise

    def get_state(self) -> AgentState:
        """Get current agent state.

        Returns:
            Current agent state.
        """
        return self.state

    def get_execution_time(self) -> float | None:
        """Get execution time in seconds.

        Returns:
            Execution time or None if not completed.
        """
        return self.execution_time

