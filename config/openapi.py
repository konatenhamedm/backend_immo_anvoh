"""Post-traitement du schéma OpenAPI (drf-spectacular)."""


def _refs(node, found):
    """Collecte les noms de composants référencés (`#/components/schemas/X`) dans un fragment de schéma."""
    if isinstance(node, dict):
        ref = node.get("$ref")
        if isinstance(ref, str) and ref.startswith("#/components/schemas/"):
            found.add(ref.rsplit("/", 1)[1])
        for value in node.values():
            _refs(value, found)
    elif isinstance(node, list):
        for value in node:
            _refs(value, found)


def _closure(roots, schemas):
    seen, todo = set(), list(roots)
    while todo:
        name = todo.pop()
        if name in seen or name not in schemas:
            continue
        seen.add(name)
        nested = set()
        _refs(schemas[name], nested)
        todo.extend(nested - seen)
    return seen


def mark_response_fields_required(result, generator, request, public):
    """Une réponse contient toujours tous les champs du serializer.

    drf-spectacular marque pourtant « optionnel » un champ qui a une valeur par défaut. Côté front, cela donne
    `status?: string` alors que la valeur est toujours là. On rend obligatoires les champs des composants
    atteignables depuis une réponse, sauf ceux qui servent aussi de corps de requête.
    """
    schemas = result.get("components", {}).get("schemas", {})
    in_responses, in_requests = set(), set()
    for item in result.get("paths", {}).values():
        for operation in item.values():
            if not isinstance(operation, dict):
                continue
            _refs(operation.get("responses", {}), in_responses)
            _refs(operation.get("requestBody", {}), in_requests)
    response_side = _closure(in_responses, schemas) - _closure(in_requests, schemas)
    for name in response_side:
        _require_all(schemas[name])
    return result


def _require_all(schema):
    """Rend obligatoires les propriétés d'un schéma objet, y compris les objets imbriqués décrits en ligne.

    On parcourt les *schémas* (properties → chaque schéma, items, additionalProperties, allOf…) et non tous les
    dictionnaires : un champ peut légitimement s'appeler « properties » ou « required ».
    """
    if not isinstance(schema, dict):
        return
    props = schema.get("properties")
    if isinstance(props, dict) and props:
        schema["required"] = sorted(set(schema.get("required", [])) | set(props))
        for sub in props.values():
            _require_all(sub)
    _require_all(schema.get("items"))
    _require_all(schema.get("additionalProperties"))
    for key in ("allOf", "oneOf", "anyOf"):
        for sub in schema.get(key, []) or []:
            _require_all(sub)
