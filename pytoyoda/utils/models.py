"""Utilities for manipulating or extending pydantic models."""

from collections.abc import Callable
from types import UnionType
from typing import Annotated, Any, Generic, TypeVar, Union, get_args, get_origin

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


def _unwrap_optional(annotation: Any) -> Any:  # noqa: ANN401
    """Return the non-None member of ``X | None`` / ``Optional[X]``, else the input."""
    origin = get_origin(annotation)
    if origin in (Union, UnionType):
        args = [arg for arg in get_args(annotation) if arg is not type(None)]
        if len(args) == 1:
            return args[0]
    return annotation


def _list_item_model(annotation: Any) -> type[BaseModel] | None:  # noqa: ANN401
    """Return the item model type if annotation is ``list[SomeBaseModel]``."""
    unwrapped = _unwrap_optional(annotation)
    if get_origin(unwrapped) is not list:
        return None
    args = get_args(unwrapped)
    if len(args) != 1:
        return None
    (item_type,) = args
    if isinstance(item_type, type) and issubclass(item_type, BaseModel):
        return item_type
    return None


def make_invalid_items_to_none(item_type: type[BaseModel]) -> Callable[..., Any]:
    """Build a wrap validator that drops only the invalid items of a list.

    Unlike :func:`invalid_to_none` applied to the whole list field - which
    discards *every* item the moment a single one fails validation - this
    validates each item independently so one malformed entry (e.g. one
    vehicle with an unexpected field) doesn't erase the rest of the list.

    Args:
        item_type: The pydantic model each list item should validate against.

    Returns:
        A callable suitable for use as a Pydantic ``WrapValidator`` handler.

    """

    def _validate_item(item: Any) -> BaseModel | None:  # noqa: ANN401
        """Return the validated item, or None if it fails validation."""
        try:
            return item if isinstance(item, item_type) else item_type(**item)
        except (ValidationError, TypeError):
            return None

    def validator(v: Any, handler: Callable[[Any], Any]) -> Any:  # noqa: ANN401
        if not isinstance(v, list):
            # Not a list at all (None, wrong type, etc.) - fall back to the
            # existing whole-field behavior.
            return invalid_to_none(v, handler)

        # Skip only the items that fail validation; the rest of the list
        # survives.
        valid_items = [
            validated for item in v if (validated := _validate_item(item)) is not None
        ]
        try:
            return handler(valid_items)
        except ValidationError:
            return None

    return validator


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
        It adds the invalid_to_none validator to each field annotation. Fields
        typed as ``list[SomeCustomEndpointBaseModel] | None`` get a per-item
        tolerant validator instead, so a single malformed list item doesn't
        collapse the entire list to None.
        """
        for name, annotation in cls.__annotations__.items():
            # Skip private/protected attributes
            if name.startswith("_"):
                continue

            # Handle already Annotated fields
            if get_origin(annotation) is Annotated:
                base_annotation = get_args(annotation)[0]
            else:
                base_annotation = annotation

            item_type = _list_item_model(base_annotation)
            if item_type is not None:
                validator = WrapValidator(make_invalid_items_to_none(item_type))
            else:
                validator = WrapValidator(invalid_to_none)

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

    value: float | None
    unit: str | None

    def __str__(self) -> str:
        """Represent Temperature model as string."""
        return f"{self.value}{self.unit}"


class Distance(BaseModel):
    """Distance value with unit."""

    value: float | None
    unit: str | None

    def __str__(self) -> str:
        """Represent Distance model as string."""
        return f"{self.value} {self.unit}"
