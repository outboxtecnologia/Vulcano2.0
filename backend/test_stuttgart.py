"""Testa a metragem do Stuttgart (cno=8734)."""
from main import get_sero_maodeobra

# Consolidado
r_all = get_sero_maodeobra(empresa_id=959, ano=2025, mes=12)
print(f"Consolidado — area_total: {r_all['resumo']['area_total']} m²")

# Stuttgart apenas
r_stutt = get_sero_maodeobra(empresa_id=959, ano=2025, mes=12, cno=8734)
print(f"Stuttgart   — area_total: {r_stutt['resumo']['area_total']} m²")
print(f"Stuttgart   — mao_obra:   {r_stutt['resumo']['mao_de_obra']}")
print(f"Stuttgart   — total_inss: {r_stutt['resumo']['total_inss']}")
