from typing import Any, Dict

from dlt.common.schema.schema import Schema
from dlt.common.storages.schema_storage import SchemaStorage
from dlt.common.configuration.specs import SchemaVolumeConfiguration


class LiveSchemaStorage(SchemaStorage):

    def __init__(self, C: SchemaVolumeConfiguration = None, makedirs: bool = False) -> None:
        self.live_schemas: Dict[str, Schema] = {}
        super().__init__(C, makedirs)

    def __getitem__(self, name: str) -> Schema:
        # disconnect live schema
        self.live_schemas.pop(name, None)
        # return new schema instance
        schema = super().load_schema(name)
        self._update_live_schema(schema, True)

        return schema

    def load_schema(self, name: str) -> Schema:
        self.commit_live_schema(name)
        # now live schema is saved so we can load it
        return super().load_schema(name)

    def save_schema(self, schema: Schema) -> str:
        rv = super().save_schema(schema)
        # update the live schema with schema being saved but to not create live instance if not already present
        self._update_live_schema(schema, False)
        return rv

    def commit_live_schema(self, name: str) -> Schema:
        # if live schema exists and is modified then it must be used as an import schema
        live_schema = self.live_schemas.get(name)
        if live_schema and live_schema.stored_version_hash != live_schema.version_hash:
            live_schema.bump_version()
            if self.C.import_schema_path:
                # overwrite import schemas if specified
                self._export_schema(live_schema, self.C.import_schema_path)
            else:
                # write directly to schema storage if no import schema folder configured
                self._save_schema(live_schema)
        return live_schema

    def _update_live_schema(self, schema: Schema, can_create_new: bool) -> None:
        if schema.name in self.live_schemas:
            # replace content without replacing instance
            self.live_schemas[schema.name].from_dict(schema.to_dict())  # type: ignore
        elif can_create_new:
            self.live_schemas[schema.name] = schema
