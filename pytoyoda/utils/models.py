"""Utilities for manipulating or extending pydantic models."""

# ruff: noqa: FA100

from collections.abc import Callable
from typing import Annotated, Any, Generic, Optional, TypeVar, get_args, get_origin

from pydantic import BaseModel, ConfigDict, ValidationError, WrapValidator

T = TypeVar("T")


def invalid_to_none(v: Any, handler: Callable[[Any], Any]) -> Any:  # noqa : ANN401
    """Return None for failed validations otherwise original value.

    Args:
        v: Value to validate
        handler: Original validation handler

    Returns:
        Validated value or None if validation fails

    """
    try:
        return handler(v)
    except ValidationError:
        return None


class CustomEndpointBaseModel(BaseModel):
    """Enhanced BaseModel that automatically sets invalid values to None.

    This model extends Pydantic's BaseModel to provide more graceful handling
    of invalid data by converting fields that fail validation to None instead
    of raising exceptions.

    Example:
        >>> class User(CustomBaseModel):
        ...     name: str
        ...     age: int
        >>> # This won't raise an error, age will be None
        >>> user = User(name="John", age="not-a-number")
        >>> print(user.age)
        None

    """

    def __init_subclass__(cls, **kwargs: dict) -> None:
        """Automatically add validation wrapper to all fields of subclasses.

        This method is called when a subclass of CustomBaseModel is created.
        It adds the invalid_to_none validator to each field annotation.
        """
        for name, annotation in cls.__annotations__.items():
            # Skip private/protected attributes
            if name.startswith("_"):
                continue

            # Apply the validator wrapper
            validator = WrapValidator(invalid_to_none)

            # Handle already Annotated fields
            if get_origin(annotation) is Annotated:
                cls.__annotations__[name] = Annotated[get_args(annotation), validator]
            else:
                cls.__annotations__[name] = Annotated[annotation, validator]


class CustomAPIBaseModel(BaseModel, Generic[T]):
    """Base class for all API models."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def __init__(self, data: T, **kwargs: dict) -> None:
        """Initialize with data object.

        Args:
            data (T): The underlying data object
            **kwargs: Additional keyword arguments passed to the parent class

        """
        super().__init__(**kwargs)
        self._data = data

    def __repr__(self) -> str:
        """Generate string representation based on properties."""
        return " ".join(
            [
                f"{k}={getattr(self, k)!s}"
                for k, v in type(self).__dict__.items()
                if isinstance(v, property)
            ],
        )


class Temperature(BaseModel):
    """Temperature value with unit."""

    value: Optional[float]
    unit: Optional[str]

    def __str__(self) -> str:
        """Represent Temperature model as string."""
        return f"{self.value}{self.unit}"


class Distance(BaseModel):
    """Distance value with unit."""

    value: Optional[float]
    unit: Optional[str]

    def __str__(self) -> str:
        """Represent Distance model as string."""
        return f"{self.value} {self.unit}"
