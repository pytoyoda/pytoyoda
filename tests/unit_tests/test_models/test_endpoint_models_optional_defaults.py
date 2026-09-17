"""Regression guard for the systemic 'required Optional field' bug pattern.

See #282, #287, #229, #284, #285 and #259: ``CustomEndpointBaseModel``
subclasses that declare a field as ``X | None`` without ``default=None`` are
still *required* to Pydantic. Because ``CustomEndpointBaseModel`` wraps every
field with ``WrapValidator(invalid_to_none)``, a single missing key on such a
field silently collapses the *entire containing object* (and, when nested in
a list, potentially the whole list) to ``None`` instead of surfacing an
error - so Toyota's API omitting/renaming a field goes completely unnoticed.

This test walks every ``CustomEndpointBaseModel`` subclass reachable from the
public endpoint models and fails if any nullable field lacks a default,
preventing the whole class of bug from being reintroduced (mechanically or
otherwise) for any endpoint model, present or future.
"""

from __future__ import annotations

import importlib
import pkgutil
import typing
from types import UnionType

import pytoyoda.models.endpoints
from pytoyoda.utils.models import CustomEndpointBaseModel


def _iter_endpoint_modules() -> typing.Iterator[str]:
    package = pytoyoda.models.endpoints
    for module_info in pkgutil.iter_modules(package.__path__, f"{package.__name__}."):
        yield module_info.name


def _iter_custom_endpoint_models() -> typing.Iterator[type[CustomEndpointBaseModel]]:
    seen: set[type[CustomEndpointBaseModel]] = set()
    for module_name in _iter_endpoint_modules():
        module = importlib.import_module(module_name)
        for attr in vars(module).values():
            if (
                isinstance(attr, type)
                and issubclass(attr, CustomEndpointBaseModel)
                and attr is not CustomEndpointBaseModel
                and attr not in seen
            ):
                seen.add(attr)
                yield attr


def _is_optional(annotation: object) -> bool:
    """Return True if the annotation allows None (``X | None``/Optional[X])."""
    origin = typing.get_origin(annotation)
    if origin is UnionType or origin is typing.Union:
        return type(None) in typing.get_args(annotation)
    return False


# A handful of fields are *deliberately* required via ``Field(..., alias=...)``
# (Pydantic's explicit "no default" sentinel) rather than accidentally
# required by a forgotten default. These echo request parameters or
# always-present metadata rather than optional API data, so they're kept as
# an explicit, reviewed allowlist instead of being auto-defaulted.
KNOWN_INTENTIONALLY_REQUIRED = {
    "pytoyoda.models.endpoints.trips._ScoresModel.global_",
    "pytoyoda.models.endpoints.trips.TripsModel.from_date",
    "pytoyoda.models.endpoints.trips.TripsModel.to_date",
    "pytoyoda.models.endpoints.trips.TripsModel.metadata",
}


def test_no_required_optional_fields_in_endpoint_models() -> None:
    """Every nullable field on a CustomEndpointBaseModel must default to None."""
    offenders = []
    for model in _iter_custom_endpoint_models():
        for field_name, field_info in model.model_fields.items():
            if not _is_optional(field_info.annotation):
                continue
            if not field_info.is_required():
                continue
            qualname = f"{model.__module__}.{model.__qualname__}.{field_name}"
            if qualname in KNOWN_INTENTIONALLY_REQUIRED:
                continue
            offenders.append(qualname)

    assert offenders == [], (
        "Nullable fields must set default=None, otherwise "
        "CustomEndpointBaseModel's invalid_to_none wrapper silently collapses "
        f"the whole containing object when Toyota's API omits them: {offenders}"
    )
