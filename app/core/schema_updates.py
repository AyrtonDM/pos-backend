from sqlalchemy import text

from app.core.database import engine


def apply_schema_updates() -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                ALTER TABLE usuario_rol
                ADD COLUMN IF NOT EXISTS id_sucursal INTEGER
                """
            )
        )
        connection.execute(
            text(
                """
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1
                        FROM pg_constraint
                        WHERE conname = 'fk_usuario_rol_sucursal'
                    ) THEN
                        ALTER TABLE usuario_rol
                        ADD CONSTRAINT fk_usuario_rol_sucursal
                        FOREIGN KEY (id_sucursal)
                        REFERENCES sucursal(id_sucursal);
                    END IF;
                END $$;
                """
            )
        )
