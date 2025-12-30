from flask import url_for


def validate_hateoas_links(links, expected_rels_map):
    """
    expected_rels_map: { 
        "self": ("GET", "userresource", {"user_id": 1}),
        "tasks": ("GET", "tasksresource", {"user_id": 1}) 
    }
    """
    link_map = {link["rel"]: link for link in links}
    
    for rel, (method, endpoint, params) in expected_rels_map.items():
        assert rel in link_map, f"Missing rel: {rel}"
        assert link_map[rel]["method"] == method
        assert link_map[rel]["href"] == url_for(endpoint, **params)
        