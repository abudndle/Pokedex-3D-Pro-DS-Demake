"""C162: fail-closed validation for source draw-pass staging, not a renderer."""
def validate_manifest(m):
    if m.get("schema")!="p3d-source-draw-pass-v1" or m.get("sampler_roles_verified") is not False or m.get("native_renderer_integrated") is not False:
        raise ValueError("unverified source or renderer status")
    n=m.get("mesh_count")
    if type(n)!=int or not 1<=n<=1000 or not isinstance(m.get("draws"),list) or not m["draws"]:
        raise ValueError("invalid manifest")
    primary=[set() for _ in range(n)]
    secondary=[set() for _ in range(n)]
    for i,row in enumerate(m["draws"]):
        if row.get("order")!=i: raise ValueError("draw order mismatch")
        mesh,mat,tri=row.get("mesh"),row.get("material"),row.get("triangles")
        if any(type(x)!=int for x in (mesh,mat,tri)) or not (0<=mesh<n and 0<=mat<=255 and 0<tri<=65535):
            raise ValueError("invalid draw fields")
        if row.get("pass")=="primary":primary[mesh].add(mat)
        elif row.get("pass")=="secondary":secondary[mesh].add(mat)
        else:raise ValueError("unknown draw pass")
    if any(len(p)>1 or not (p or s) for p,s in zip(primary,secondary)):
        raise ValueError("ambiguous or missing draw")
    secondary_only=[i for i in range(n) if not primary[i] and secondary[i]]
    if m.get("secondary_only_meshes")!=secondary_only:
        raise ValueError("secondary-only roster mismatch")
    return {"draws":len(m["draws"]),"secondary_only_meshes":secondary_only,
            "texture_binding_allowed":False,"native_rendering_proven":False}
