import requests

# Test API RPPS (Répertoire Partagé des Professionnels de Santé) — data.gouv.fr
r = requests.get(
    'https://public.opendatasoft.com/api/explore/v2.1/catalog/datasets/finess-etablissement/records',
    params={
        'where': "libcategetab like 'Psychiatrie' AND libdepartement like 'Paris'",
        'limit': 3
    }
)
print("FINESS Status:", r.status_code)
print("Résultats:", len(r.json().get('results', [])))
for rec in r.json().get('results', []):
    print(f"  - {rec.get('rs')} | {rec.get('adresse')} | {rec.get('libdepartement')}")

print()

# Test API Annuaire RPPS correct
r2 = requests.get(
    'https://public.opendatasoft.com/api/explore/v2.1/catalog/datasets/finess-etablissement/records',
    params={'limit': 2}
)
data2 = r2.json()
print("Champs FINESS:")
if data2.get('results'):
    for k, v in data2['results'][0].items():
        print(f"  {k}: {v}")