"""Tests for `BaseModel.model_serialization_field_conflicts`."""

import dataclasses

import pytest

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SerializationFieldConflict,
    computed_field,
    create_model,
    model_serializer,
)
from pydantic.alias_generators import to_camel


def test_no_conflict_returns_empty_list() -> None:
    class Model(BaseModel):
        a: int
        b: int = Field(serialization_alias='b_alias')

    assert Model.model_serialization_field_conflicts(by_alias=False) == []
    assert Model.model_serialization_field_conflicts(by_alias=True) == []


def test_empty_model_and_base_model() -> None:
    class Empty(BaseModel):
        pass

    assert Empty.model_serialization_field_conflicts(by_alias=True) == []
    assert BaseModel.model_serialization_field_conflicts(by_alias=False) == []


def test_explicit_serialization_alias_conflict() -> None:
    class User(BaseModel):
        name: str = Field(serialization_alias='identifier')
        identifier: int

    by_alias = User.model_serialization_field_conflicts(by_alias=True)
    assert len(by_alias) == 1
    conflict = by_alias[0]
    assert isinstance(conflict, SerializationFieldConflict)
    assert conflict.output_key == 'identifier'
    # Both fields write to the same key, listed in declaration order:
    assert conflict.field_names == ['name', 'identifier']
    assert conflict.conditional_field_names == []

    # Field names are distinct, so dumping by name can never collide:
    assert User.model_serialization_field_conflicts(by_alias=False) == []


def test_plain_alias_is_used_as_serialization_alias() -> None:
    class Model(BaseModel):
        a: int = Field(alias='k')
        k: int = 1

    conflicts = Model.model_serialization_field_conflicts(by_alias=True)
    assert [(c.output_key, c.field_names) for c in conflicts] == [('k', ['a', 'k'])]


def test_generated_alias_conflict() -> None:
    class Model(BaseModel):
        model_config = ConfigDict(alias_generator=to_camel)

        foo_bar: int
        fooBar: int = 2

    # The check uses the final field configuration, i.e. the alias generated for `foo_bar`:
    conflicts = Model.model_serialization_field_conflicts(by_alias=True)
    assert [(c.output_key, c.field_names) for c in conflicts] == [('fooBar', ['foo_bar', 'fooBar'])]

    # By name the two declared fields are still distinct:
    assert Model.model_serialization_field_conflicts(by_alias=False) == []


def test_inherited_fields_and_declaration_order() -> None:
    class Parent(BaseModel):
        p_dup: int = Field(serialization_alias='dup')
        own: int

    class Child(Parent):
        c_dup: int = Field(serialization_alias='dup')
        after: int = Field(serialization_alias='own')

    conflicts = Child.model_serialization_field_conflicts(by_alias=True)

    # Conflicts are ordered by the first field declaring each output key, fields within a group
    # follow the (inheritance-aware) field declaration order:
    assert [(c.output_key, c.field_names) for c in conflicts] == [
        ('dup', ['p_dup', 'c_dup']),
        ('own', ['own', 'after']),
    ]


def test_multiple_conflicts_are_ordered_by_first_occurrence() -> None:
    class Model(BaseModel):
        a: int = Field(serialization_alias='x')
        b: int = Field(serialization_alias='y')
        x: int = 1
        y: int = 2

    conflicts = Model.model_serialization_field_conflicts(by_alias=True)
    assert [(c.output_key, c.field_names) for c in conflicts] == [
        ('x', ['a', 'x']),
        ('y', ['b', 'y']),
    ]


def test_permanently_excluded_fields_do_not_participate() -> None:
    class Model(BaseModel):
        a: int = Field(serialization_alias='b', exclude=True)
        b: int

    assert Model.model_serialization_field_conflicts(by_alias=True) == []
    assert Model.model_serialization_field_conflicts(by_alias=False) == []

    # Sanity check: `a` really is never serialized:
    assert Model.model_construct(a=1, b=2).model_dump(by_alias=True) == {'b': 2}


def test_conditional_exclude_if_participates_conservatively() -> None:
    class Model(BaseModel):
        a: int = Field(serialization_alias='b', exclude_if=lambda value: value == 0)
        b: int

    conflicts = Model.model_serialization_field_conflicts(by_alias=True)
    assert len(conflicts) == 1
    conflict = conflicts[0]
    assert conflict.output_key == 'b'
    assert conflict.field_names == ['a', 'b']
    # `a` is flagged as conditional: whether it actually collides depends on its runtime value.
    # The check itself stays conservative and never decides (or observes) that outcome:
    assert conflict.conditional_field_names == ['a']

    # For completeness, `exclude_if` still drives the actual serialization as usual:
    assert Model(a=1, b=2).model_dump(by_alias=True) == {'b': 2}
    assert Model(a=0, b=2).model_dump(by_alias=True) == {'b': 2}


def test_exclude_if_callable_is_never_called() -> None:
    calls: list[int] = []

    def exclude_if(value: int) -> bool:
        calls.append(value)
        return False

    class Model(BaseModel):
        a: int = Field(serialization_alias='b', exclude_if=exclude_if)
        b: int

    Model.model_serialization_field_conflicts(by_alias=True)
    Model.model_serialization_field_conflicts(by_alias=False)
    assert calls == []


def test_field_name_mode_ignores_aliases() -> None:
    class Model(BaseModel):
        a: int = Field(serialization_alias='b')
        b: int = Field(alias='c')

    # Aliases are ignored in field-name mode, so there is nothing to report:
    assert Model.model_serialization_field_conflicts(by_alias=False) == []


def test_alias_equal_to_own_field_name_is_not_a_self_conflict() -> None:
    class Model(BaseModel):
        a: int = Field(alias='a')
        b: int

    assert Model.model_serialization_field_conflicts(by_alias=True) == []


def test_computed_fields_extra_and_custom_model_serializer_are_out_of_scope() -> None:
    class Model(BaseModel):
        model_config = ConfigDict(extra='allow')

        a: int = Field(serialization_alias='shared')
        b: int = Field(serialization_alias='shared')

        @computed_field
        def shared(self) -> int:
            return 3

        @model_serializer
        def _custom_serializer(self) -> dict[str, int]:
            raise AssertionError('custom model serializers must not be executed by the check')

    conflicts = Model.model_serialization_field_conflicts(by_alias=True)
    assert [(c.output_key, c.field_names) for c in conflicts] == [('shared', ['a', 'b'])]
    # Computed fields are not reported even though `shared` would also be emitted at runtime:
    assert conflicts[0].field_names == ['a', 'b']


def test_check_does_not_instantiate_model_or_call_default_factory() -> None:
    created = []

    def factory() -> int:
        created.append('called')
        return 1

    class Model(BaseModel):
        required_field: int
        with_factory: int = Field(default_factory=factory)

    # No instance is created (the required field is not provided) and the factory is not called:
    assert Model.model_serialization_field_conflicts(by_alias=True) == []
    assert created == []


def test_check_does_not_change_model_dump_behavior() -> None:
    class Model(BaseModel):
        a: int = Field(serialization_alias='shared')
        b: int = Field(serialization_alias='shared')

    # Running the check leaves the serializer untouched:
    Model.model_serialization_field_conflicts(by_alias=True)
    assert Model(a=1, b=2).model_dump(by_alias=True) == {'shared': 2}
    assert Model(a=1, b=2).model_dump(by_alias=False) == {'a': 1, 'b': 2}


def test_dynamic_model_is_supported() -> None:
    Model = create_model(
        'DynamicModel',
        a=(int, Field(serialization_alias='k')),
        k=(int, 1),
    )

    assert [(c.output_key, c.field_names) for c in Model.model_serialization_field_conflicts(by_alias=True)] == [
        ('k', ['a', 'k'])
    ]


def test_generic_parametrized_model_uses_final_fields() -> None:
    from typing import Generic, TypeVar

    T = TypeVar('T')

    class GenericModel(BaseModel, Generic[T]):
        a: T = Field(serialization_alias='b')
        b: int

    Parametrized = GenericModel[int]

    assert [(c.output_key, c.field_names) for c in Parametrized.model_serialization_field_conflicts(by_alias=True)] == [
        ('b', ['a', 'b'])
    ]


def test_result_is_a_frozen_dataclass() -> None:
    class Model(BaseModel):
        a: int = Field(serialization_alias='k')
        k: int

    conflict = Model.model_serialization_field_conflicts(by_alias=True)[0]

    assert dataclasses.is_dataclass(conflict)
    assert conflict.output_key == 'k'
    assert conflict.field_names == ['a', 'k']
    assert conflict.conditional_field_names == []
    with pytest.raises(dataclasses.FrozenInstanceError):
        conflict.output_key = 'other'  # type: ignore[misc]


def test_by_alias_is_a_required_keyword_only_argument() -> None:
    class Model(BaseModel):
        a: int

    with pytest.raises(TypeError, check=lambda err: 'by_alias' in str(err)):
        Model.model_serialization_field_conflicts()  # type: ignore[call-arg]

    with pytest.raises(TypeError):
        Model.model_serialization_field_conflicts(True)  # type: ignore[misc]
