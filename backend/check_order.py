import main

for match_index, route in enumerate(main.app.routes):
    path = getattr(route, 'path', route.name)
    print(f"{match_index}: {path}")
