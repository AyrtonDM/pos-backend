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
        connection.execute(
            text(
                """
                ALTER TABLE movimiento_inventario
                ADD COLUMN IF NOT EXISTS id_usuario INTEGER
                """
            )
        )
        connection.execute(
            text(
                """
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1
                        FROM information_schema.columns
                        WHERE table_name = 'movimiento_caja'
                          AND column_name = 'id_metodo_pago'
                          AND is_nullable = 'NO'
                    ) THEN
                        ALTER TABLE movimiento_caja ALTER COLUMN id_metodo_pago DROP NOT NULL;
                    END IF;
                END $$;
                """
            )
        )
        connection.execute(
            text(
                """
                ALTER TABLE movimiento_caja
                ADD COLUMN IF NOT EXISTS monto NUMERIC(12, 2) DEFAULT 0,
                ADD COLUMN IF NOT EXISTS concepto TEXT
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
                        WHERE conname = 'fk_movimiento_inventario_usuario'
                    ) THEN
                        ALTER TABLE movimiento_inventario
                        ADD CONSTRAINT fk_movimiento_inventario_usuario
                        FOREIGN KEY (id_usuario)
                        REFERENCES usuario(id_usuario);
                    END IF;
                END $$;
                """
            )
        )
        connection.execute(
            text(
                """
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1
                        FROM information_schema.columns
                        WHERE table_name = 'venta'
                          AND column_name = 'id_cliente'
                          AND is_nullable = 'NO'
                    ) THEN
                        ALTER TABLE venta ALTER COLUMN id_cliente DROP NOT NULL;
                    END IF;
                END $$;
                """
            )
        )
        connection.execute(
            text(
                """
                ALTER TABLE caja_sesion
                ADD COLUMN IF NOT EXISTS id_usuario INTEGER
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
                        WHERE conname = 'fk_caja_sesion_usuario'
                    ) THEN
                        ALTER TABLE caja_sesion
                        ADD CONSTRAINT fk_caja_sesion_usuario
                        FOREIGN KEY (id_usuario)
                        REFERENCES usuario(id_usuario);
                    END IF;
                END $$;
                """
            )
        )
        connection.execute(
            text(
                """
                ALTER TABLE categoria_producto
                ADD COLUMN IF NOT EXISTS id_empresa INTEGER
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
                        WHERE conname = 'fk_categoria_producto_empresa'
                    ) THEN
                        ALTER TABLE categoria_producto
                        ADD CONSTRAINT fk_categoria_producto_empresa
                        FOREIGN KEY (id_empresa)
                        REFERENCES empresa(id_empresa);
                    END IF;
                END $$;
                """
            )
        )
        connection.execute(
            text(
                """
                ALTER TABLE producto
                DROP COLUMN IF EXISTS costo,
                ADD COLUMN IF NOT EXISTS id_empresa INTEGER,
                ADD COLUMN IF NOT EXISTS id_subcategoria INTEGER,
                ADD COLUMN IF NOT EXISTS codigo_barra VARCHAR(100),
                ADD COLUMN IF NOT EXISTS descripcion TEXT,
                ADD COLUMN IF NOT EXISTS unidad_medida VARCHAR(50),
                ADD COLUMN IF NOT EXISTS imagen VARCHAR(255),
                ADD COLUMN IF NOT EXISTS activo BOOLEAN DEFAULT TRUE
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
                        WHERE conname = 'fk_producto_empresa'
                    ) THEN
                        ALTER TABLE producto
                        ADD CONSTRAINT fk_producto_empresa
                        FOREIGN KEY (id_empresa)
                        REFERENCES empresa(id_empresa);
                    END IF;
                END $$;
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
                        WHERE conname = 'fk_producto_subcategoria'
                    ) THEN
                        ALTER TABLE producto
                        ADD CONSTRAINT fk_producto_subcategoria
                        FOREIGN KEY (id_subcategoria)
                        REFERENCES subcategoria_producto(id_subcategoria);
                    END IF;
                END $$;
                """
            )
        )
        connection.execute(
            text(
                """
                ALTER TABLE usuario_rol
                DROP CONSTRAINT IF EXISTS uq_usuario_rol
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
                        WHERE conname = 'uq_usuario_rol_sucursal'
                    ) THEN
                        ALTER TABLE usuario_rol
                        ADD CONSTRAINT uq_usuario_rol_sucursal
                        UNIQUE (id_usuario, id_rol, id_empresa, id_sucursal);
                    END IF;
                END $$;
                """
            )
        )
        # Asegurar que saldo_credito y limite_credito permiten NULL
        connection.execute(
            text(
                """
                DO $$
                BEGIN
                    -- quitar NOT NULL si existe
                    IF EXISTS (
                        SELECT 1
                        FROM information_schema.columns
                        WHERE table_name='cliente' AND column_name='saldo_credito' AND is_nullable='NO'
                    ) THEN
                        ALTER TABLE cliente ALTER COLUMN saldo_credito DROP NOT NULL;
                    END IF;
                    IF EXISTS (
                        SELECT 1
                        FROM information_schema.columns
                        WHERE table_name='cliente' AND column_name='limite_credito' AND is_nullable='NO'
                    ) THEN
                        ALTER TABLE cliente ALTER COLUMN limite_credito DROP NOT NULL;
                    END IF;
                END $$;
                """
            )
        )
        connection.execute(
            text(
                """
                ALTER TABLE detalle_venta
                ADD COLUMN IF NOT EXISTS descripcion TEXT
                """
            )
        )
        # ---------------------------------------------------------------
        # Stripe Checkout — trazabilidad e idempotencia en historial_suscripcion
        # ---------------------------------------------------------------
        connection.execute(
            text(
                """
                ALTER TABLE historial_suscripcion
                ADD COLUMN IF NOT EXISTS stripe_session_id         VARCHAR(255),
                ADD COLUMN IF NOT EXISTS stripe_payment_intent_id  VARCHAR(255),
                ADD COLUMN IF NOT EXISTS stripe_payment_status     VARCHAR(50)
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
                        WHERE conname = 'uq_historial_suscripcion_stripe_session'
                    ) THEN
                        ALTER TABLE historial_suscripcion
                        ADD CONSTRAINT uq_historial_suscripcion_stripe_session
                        UNIQUE (stripe_session_id);
                    END IF;
                END $$;
                """
            )
        )
