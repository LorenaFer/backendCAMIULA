"""TDD — FormSchema domain entity tests."""

import pytest


class TestFormSchemaEntity:
    def test_create_with_required_fields(self):
        from app.modules.form_schemas.domain.entities.form_schema import FormSchema

        schema = FormSchema(
            id="medicina-general-v1",
            version="1.0",
            specialty_id="medicina-general",
            specialty_name="Medicina General",
            schema_json={"id": "medicina-general-v1", "sections": []},
        )
        assert schema.id == "medicina-general-v1"
        assert schema.specialty_id == "medicina-general"
        assert schema.version == "1.0"

    def test_normalize_specialty_name(self):
        from app.modules.form_schemas.domain.entities.form_schema import FormSchema

        assert FormSchema.normalize_name("Medicina General") == "medicina-general"
        assert FormSchema.normalize_name("Odontología") == "odontologia"
        assert FormSchema.normalize_name("Cirugía General") == "cirugia-general"
        assert FormSchema.normalize_name("Control Prenatal") == "control-prenatal"
        assert FormSchema.normalize_name("ORL") == "orl"

    def test_validate_requires_id(self):
        from app.modules.form_schemas.domain.entities.form_schema import FormSchema

        schema = FormSchema(
            id="test-v1",
            version="1.0",
            specialty_id="test",
            specialty_name="Test",
            schema_json={"id": "test-v1", "sections": []},
        )
        schema.validate()  # should not raise

    def test_validate_raises_if_schema_json_missing_sections(self):
        from app.modules.form_schemas.domain.entities.form_schema import FormSchema

        schema = FormSchema(
            id="test-v1",
            version="1.0",
            specialty_id="test",
            specialty_name="Test",
            schema_json={"id": "test-v1"},  # missing sections
        )
        with pytest.raises(ValueError, match="sections"):
            schema.validate()
