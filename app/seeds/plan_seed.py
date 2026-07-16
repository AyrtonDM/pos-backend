import logging
from decimal import Decimal
from sqlalchemy.orm import Session
from app.models.empresas.plan import Plan
from app.models.empresas.plan_modulo import PlanModulo
from app.models.usuarios.modulo import Modulo
logger = logging.getLogger(__name__)
DEFAULT_PLANES = [
    {
        "nombre": "Básico",
        "descripcion": "Plan ideal para emprendedores y pequeños negocios.",
        "precio": Decimal("29.99"),
        "modulos": ["USUARIOS", "INVENTARIO", "VENTAS", "CAJAS"]
    },
    {
        "nombre": "Pro",
        "descripcion": "Plan diseñado para medianas empresas con mayores necesidades.",
        "precio": Decimal("59.99"),
        "modulos": ["USUARIOS", "EMPRESAS", "INVENTARIO", "VENTAS", "CLIENTES", "CAJAS"]
    },
    {
        "nombre": "Premium",
        "descripcion": "Plan completo con todas las características del sistema.",
        "precio": Decimal("99.99"),
        "modulos": ["USUARIOS", "EMPRESAS", "INVENTARIO", "VENTAS", "CLIENTES", "CAJAS", "REPORTES"]
    }
]
def seed_planes(db: Session) -> None:
    for plan_data in DEFAULT_PLANES:
        try:
            # Buscar plan por nombre para hacer el seed idempotente
            plan = db.query(Plan).filter(Plan.nombre == plan_data["nombre"]).first()
            if not plan:
                plan = Plan(
                    nombre=plan_data["nombre"],
                    descripcion=plan_data["descripcion"],
                    precio=plan_data["precio"]
                )
                db.add(plan)
                db.flush()  # Obtener el id_plan sin hacer commit
                print(f"[SEED PLAN] creado: {plan.nombre}")
            else:
                print(f"[SEED PLAN] ya existe: {plan.nombre}")
            
            # Asociar módulos al plan
            for codigo_modulo in plan_data["modulos"]:
                modulo = db.query(Modulo).filter(Modulo.codigo == codigo_modulo).first()
                if not modulo:
                    print(f"[SEED ERROR] Módulo no encontrado: {codigo_modulo}")
                    continue
                
                # Verificar si ya existe la relación
                relacion_existe = db.query(PlanModulo).filter(
                    PlanModulo.id_plan == plan.id_plan,
                    PlanModulo.id_modulo == modulo.id_modulo
                ).first()
                
                if not relacion_existe:
                    nueva_relacion = PlanModulo(
                        id_plan=plan.id_plan,
                        id_modulo=modulo.id_modulo
                    )
                    db.add(nueva_relacion)
                    print(f"[SEED PLAN_MODULO] relación creada: Plan {plan.nombre} -> Módulo {modulo.codigo}")
                else:
                    print(f"[SEED PLAN_MODULO] relación ya existe: Plan {plan.nombre} -> Módulo {modulo.codigo}")
                    
        except Exception as e:
            print(f"[SEED ERROR] Error procesando plan {plan_data['nombre']}: {e}")
            db.rollback()
            raise e
            
    db.commit()