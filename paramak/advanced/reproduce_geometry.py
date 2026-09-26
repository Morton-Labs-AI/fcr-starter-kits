#!/usr/bin/env python3
"""Reproduce the inspected R2 ordinary Paramak snapshot; never an intake tool.

Standalone adaptation of the accepted geometry reproduction tool.
Requires the bundled Paramak source and recorded scientific dependencies.
Writes a fresh output directory; review new results before accepting them.
"""
import argparse
import ast
from contextlib import redirect_stdout, redirect_stderr
from datetime import datetime, timezone
import hashlib
import importlib.metadata as md
import inspect
import itertools
import json
import math
import os
from pathlib import Path
import platform
import runpy
import shutil
import subprocess
import sys
import time

MODEL_ID = 'r2-tokamak-2026-09-05-a:model:paramak-tokamak-minimal'
MODEL_SHA = '9d08b94f40861848eebccb563326dfa9dbcc1eaf1cc643a96332582e53a62c1b'
RECIPE_SHA = '6fb5e00d9f162e8c9664eda39ee1293103c67c68701ff83f36ece57a1b862b80'
NAMES = ['layer_1', 'layer_2', 'layer_3', 'layer_4', 'layer_5', 'plasma']
COLORS = ['#32718c', '#63a5b2', '#edb66b', '#cf795b', '#967da6', '#dc5c91']
TOL = {'dimensional_m': .002, 'roundtrip_bound_m': 1e-5,
       'roundtrip_relative_volume': 1e-7, 'intersection_m3': 1e-10,
       'contact_distance_m': 1e-5, 'plasma_clearance_m': .002,
       'display_bound_m': .003, 'display_relative_volume': .003,
       'display_export_bound_m': 2e-6, 'adaptive_volume_relative_convergence': 1e-7,
       'adaptive_volume_fine_epsilon': 1e-9, 'adaptive_volume_coarse_epsilon': 1e-7}

def digest(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def write(p, obj):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text(json.dumps(obj, indent=2, allow_nan=False) + '\n')

def bounds(s, scale=1):
    from OCP.Bnd import Bnd_Box
    from OCP.BRepBndLib import BRepBndLib
    box = Bnd_Box()
    BRepBndLib.AddOptimal_s(s.wrapped, box, False, False)
    x0,y0,z0,x1,y1,z1 = box.Get()
    return [[x0*scale,y0*scale,z0*scale],[x1*scale,y1*scale,z1*scale]]

def mass(shape, tolerance=1e-9):
    from OCP.BRepGProp import BRepGProp
    from OCP.GProp import GProp_GProps
    properties = GProp_GProps()
    error = BRepGProp.VolumePropertiesGK_s(shape.wrapped, properties, tolerance, True, False)
    if error < 0:
        raise ValueError('Adaptive Gauss-Kronrod volume integration failed')
    return properties.Mass()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('output/regenerated'))
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[1]
    out = args.output.resolve()
    reports = out / 'reports'
    if out.exists():
        raise ValueError('Use a fresh output directory; previous results are evidence.')
    source = repo / 'advanced/source'
    recipe = source / 'examples/tokamak_from_plasma_minimal.py'
    assert digest(recipe) == RECIPE_SHA
    lock = json.loads((repo/'evidence/environment-lock.json').read_text())
    receipt = {'model_record_id': MODEL_ID, 'records': []}
    for row in lock['source_snapshot']:
        candidate = source / row['path']
        assert candidate.is_file(), row['path']
        if row['path'] != 'pyproject.toml':
            assert digest(candidate) == row['sha256'], row['path']
            receipt['records'].append({'restored_path': 'inputs/sources/paramak/' + row['path'],
                                      'sha256': row['sha256'], 'size_bytes': candidate.stat().st_size})
    out.mkdir(parents=True); reports.mkdir(parents=True, exist_ok=True)
    os.environ['MPLCONFIGDIR'] = str(out.parent/'matplotlib-cache')
    os.environ['XDG_CACHE_HOME'] = str(out.parent/'cache')
    import cadquery as cq
    import paramak
    import numpy as np
    import trimesh
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    from matplotlib.patches import Patch
    from PIL import Image, ImageDraw, ImageFont
    import vtk
    from vtk.util.numpy_support import numpy_to_vtk, numpy_to_vtkIdTypeArray
    import jsonschema
    model = {'components': json.loads((repo/'evidence/baseline-checks.json').read_text())['components']}
    installed = Path(paramak.__file__).parent
    source_rows = []
    for row in receipt['records']:
        rel = row['restored_path']
        if '/sources/paramak/' in rel:
            item = {'path': rel.split('/sources/paramak/', 1)[1], 'sha256': row['sha256'], 'size_bytes': row['size_bytes']}
            item['publisher_url'] = 'https://raw.githubusercontent.com/fusion-energy/paramak/cd4ecfff4aab9f30c945b45c2bfe91f6636d7219/' + item['path']
            item['remote_retrieval_tested_this_run'] = False
            if item['path'].startswith('src/paramak/'):
                actual = installed/item['path'].removeprefix('src/paramak/')
                item['installed_sha256'] = digest(actual)
                assert item['installed_sha256'] == item['sha256']
            source_rows.append(item)
    environment = {'python': sys.version, 'executable': sys.executable,
        'executable_sha256': digest(sys.executable), 'platform': platform.platform(),
        'machine': platform.machine(), 'packages': sorted([{'name':d.metadata['Name'],'version':d.version} for d in md.distributions()], key=lambda x:x['name'].lower()),
        'source_snapshot': source_rows, 'paramak_distribution_version': paramak.__version__,
        'source_revision_reported_by_packet': 'cd4ecfff4aab9f30c945b45c2bfe91f6636d7219',
        'source_scope': 'Supplied hash-verified source snapshot; not a full Git checkout. Locally built distribution version explicitly identifies snapshot.',
        'cad_adapter': 'CadQuery 2.6.0, cadquery-ocp; no build123d adapter',
        'cadquery_tessellation_implementation': inspect.getsource(cq.Shape.mesh)}
    write(reports/'environment.json', environment)
    freeze = subprocess.check_output([sys.executable,'-m','pip','freeze','--all'],text=True)
    (reports/'requirements.freeze.txt').write_text(freeze)
    write(reports/'restoration-receipt.json', receipt)
    (reports/'NOTICE.txt').write_text((source/'LICENSE').read_text()+'\n\nGenerated educational derivatives of the named Paramak source snapshot.\nNo device identity, material assignment, equilibrium, or physical validation.\n')
    results = []
    for name, elongation in [('baseline',2.0),('elongation-1p8',1.8)]:
        variant = out/name; variant.mkdir()
        if name == 'baseline':
            entrypoint = recipe
        else:
            tree = ast.parse(recipe.read_text())
            for n in ast.walk(tree):
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == 'tokamak_from_plasma':
                    for k in n.keywords:
                        if k.arg == 'elongation': k.value = ast.Constant(value=elongation)
            entrypoint = variant/'variant_recipe.py'
            entrypoint.write_text(ast.unparse(ast.fix_missing_locations(tree))+'\n')
        input_identity = {'model_id': MODEL_ID, 'model_sha256': MODEL_SHA,
                          'source_recipe_sha256': RECIPE_SHA, 'executed_recipe_sha256': digest(entrypoint),
                          'environment_sha256': digest(reports/'environment.json'),
                          'parameters': {'elongation': elongation},
                          'edit': None if name=='baseline' else {'parameter':'elongation','from':2.0,'to':1.8,'unit':'dimensionless'}}
        variant_hash = hashlib.sha256(json.dumps(input_identity,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        write(variant/'input-manifest.json', {**input_identity,'variant_hash':variant_hash})
        start = time.monotonic(); old = Path.cwd()
        print(f'Executing {name}', flush=True)
        try:
            os.chdir(variant)
            with (variant/'recipe.log').open('w') as log, redirect_stdout(log), redirect_stderr(log):
                run = runpy.run_path(str(entrypoint),run_name='__main__')
        finally:
            os.chdir(old)
        assembly = run['my_reactor']
        components = {}
        for obj, path, loc, color in assembly:
            leaf = path.split('/')[-1]
            shape = obj.val() if isinstance(obj,cq.Workplane) else obj
            components[leaf] = shape.located(loc)
        assert list(components) == NAMES, list(components)
        assert assembly.major_radius == 450 and assembly.minor_radius == 150
        assert assembly.elongation == elongation and assembly.triangularity == .55
        records, mesh_map = [], {}
        corrected = cq.Assembly(name='paramak_tokamak_minimal')
        scene = trimesh.Scene()
        for i,(component,shape) in enumerate(components.items()):
            assert shape.isValid() and len(shape.Solids())==1 and shape.Volume()>0
            mm = shape.scale(10)
            corrected.add(mm,name=component)
            component_step = variant/(component+'.physical-mm.step')
            cq.exporters.export(mm,str(component_step))
            imported = cq.importers.importStep(str(component_step)).val()
            b = np.array(bounds(shape,.01)); ib = np.array(bounds(imported,.001))
            v = mass(shape,1e-9)*1e-6; iv = mass(imported,1e-9)*1e-9
            default_v = shape.Volume()*1e-6
            coarse_v = mass(shape,1e-7)*1e-6
            roundtrip = {'valid':imported.isValid(), 'solid_count':len(imported.Solids()),
                         'maximum_bound_error_m':float(abs(b-ib).max()),
                         'relative_volume_error':abs(iv-v)/v}
            # Mesh source coordinates, then explicitly convert cm to m. CQ mesh's
            # deflection is relative; measured volume/bounds are checked separately.
            verts, faces = shape.tessellate(.0002,.025)
            vertices = np.array([x.toTuple() for x in verts])*.01
            mesh = trimesh.Trimesh(vertices=vertices,faces=np.array(faces),process=True)
            mesh.visual.vertex_colors = np.tile(np.array([int(COLORS[i][k:k+2],16) for k in (1,3,5)]+[255]),(len(mesh.vertices),1))
            mesh.metadata = {'component_id':component,'model_record_id':MODEL_ID,'variant_hash':variant_hash,'units':'m','up_axis':'Z','material_mapping':'unknown' if component!='plasma' else 'not_required_for_geometry'}
            scene.add_geometry(mesh,geom_name=component,node_name=component)
            mesh_map[component] = mesh
            mesh_check = {'vertices':len(mesh.vertices),'triangles':len(mesh.faces),
                         'watertight':bool(mesh.is_watertight), 'winding_consistent':bool(mesh.is_winding_consistent),
                         'positive_volume':bool(mesh.volume>0), 'volume_m3':float(mesh.volume),
                         'relative_volume_error':abs(float(mesh.volume)-v)/v,
                         'maximum_bound_error_m':float(abs(mesh.bounds-b).max()),
                         'mesh_processing':'trimesh process=True merges coincident face-seam vertices; CAD geometry unmodified'}
            records.append({'id':component,'role':model['components'][i]['role'],'material_mapping_status':model['components'][i]['material_mapping_status'],
                'valid':shape.isValid(),'solid_count':len(shape.Solids()),'shell_count':len(shape.Shells()),'face_count':len(shape.Faces()),'edge_count':len(shape.Edges()),
                'bounds_m':b.tolist(),'volume_m3':v,
                'volume_measurement':{'method':'OCP BRepGProp.VolumePropertiesGK(Eps=1e-9,OnlyClosed=True,IsUseSpan=False)',
                    'default_nonadaptive_m3':default_v,'adaptive_1e_minus_7_m3':coarse_v,
                    'adaptive_1e_minus_9_m3':v,'relative_convergence':abs(v-coarse_v)/v,
                    'default_relative_difference':abs(default_v-v)/v},
                'step_roundtrip':roundtrip,'display':mesh_check})
        corrected.save(str(variant/'physical_scale_mm.step'))
        raw_text = (variant/'tokamak_minimal.step').read_text()
        assert "SI_UNIT(.MILLI.,.METRE.)" in raw_text
        allshape = cq.Compound.makeCompound(list(components.values()))
        raw_import = cq.importers.importStep(str(variant/'tokamak_minimal.step')).val()
        corrected_import = cq.importers.importStep(str(variant/'physical_scale_mm.step')).val()
        physical_bounds = np.array(bounds(allshape,.01))
        actual_dims = physical_bounds[1]-physical_bounds[0]
        expected_dims = np.array([16.2,8.1,3*elongation+4.2])
        # Evaluate all 15 pairs; keep observed contacts and explicit intended sets.
        intended_contacts = {frozenset(x) for x in [('layer_1','layer_2'),('layer_2','layer_5'),('layer_3','layer_4'),('layer_4','layer_5')]}
        pairs=[]
        for (a,sa),(b,sb) in itertools.combinations(components.items(),2):
            intersection = sa.intersect(sb).Volume()*1e-6
            distance = sa.distance(sb)*.01
            pairs.append({'a':a,'b':b,'intersection_volume_m3':intersection,'minimum_distance_m':distance,
                          'intended_contact':frozenset([a,b]) in intended_contacts,
                          'observed_contact':distance <= TOL['contact_distance_m'],
                          'unintended_overlap':intersection>TOL['intersection_m3']})
        glb = variant/'display-m-zup.glb'; scene.export(str(glb))
        imported_scene = trimesh.load(str(glb),force='scene',process=False)
        exported_names = sorted(imported_scene.geometry)
        display_roundtrip = {'component_ids':exported_names,'maximum_bound_error_m':float(abs(imported_scene.bounds-scene.bounds).max())}
        for c in records:
            gm=imported_scene.geometry[c['id']]
            c['display']['glb_roundtrip_bound_error_m']=float(abs(gm.bounds-mesh_map[c['id']].bounds).max())
        # Depth-buffered native VTK rendering avoids component painter-order
        # artifacts. The z<=0 cutaway is an actual capped CAD intersection.
        font_path=Path(matplotlib.__file__).parent/'mpl-data/fonts/ttf/DejaVuSans.ttf'
        for view in ['whole','cutaway']:
            renderer=vtk.vtkRenderer();renderer.SetBackground(.955,.953,.94)
            for i,(component,mesh) in enumerate(mesh_map.items()):
                vertices, faces = mesh.vertices, mesh.faces
                if view=='cutaway':
                    cutter=cq.Workplane('XY').box(3000,3000,2000,centered=(True,True,False)).translate((0,0,-2000)).val()
                    cutshape=components[component].intersect(cutter)
                    cv,cf=cutshape.tessellate(.0003,.035)
                    vertices=np.array([v.toTuple() for v in cv])*.01;faces=np.array(cf)
                points=vtk.vtkPoints();points.SetData(numpy_to_vtk(np.asarray(vertices),deep=True))
                cells=vtk.vtkCellArray()
                cells.SetCells(len(faces),numpy_to_vtkIdTypeArray(np.column_stack((np.full(len(faces),3),faces)).astype(np.int64).ravel(),deep=True))
                poly=vtk.vtkPolyData();poly.SetPoints(points);poly.SetPolys(cells)
                normals=vtk.vtkPolyDataNormals();normals.SetInputData(poly);normals.SetFeatureAngle(35);normals.Update()
                mapper=vtk.vtkPolyDataMapper();mapper.SetInputConnection(normals.GetOutputPort())
                actor=vtk.vtkActor();actor.SetMapper(mapper)
                actor.GetProperty().SetColor(*[int(COLORS[i][k:k+2],16)/255 for k in (1,3,5)])
                actor.GetProperty().SetAmbient(.25);actor.GetProperty().SetDiffuse(.75)
                renderer.AddActor(actor)
            camera=renderer.GetActiveCamera();camera.SetPosition(17,-28,18);camera.SetFocalPoint(0,3,0 if view=='whole' else -1.6);camera.SetViewUp(0,0,1)
            camera.ParallelProjectionOn();camera.SetParallelScale(10.0)
            window=vtk.vtkRenderWindow();window.SetOffScreenRendering(1);window.SetMultiSamples(4);window.AddRenderer(renderer);window.SetSize(1400,850)
            window.Render()
            grab=vtk.vtkWindowToImageFilter();grab.SetInput(window);grab.ReadFrontBufferOff();grab.Update()
            writer=vtk.vtkPNGWriter();writer.SetFileName(str(variant/(view+'.render.png')));writer.SetInputConnection(grab.GetOutputPort());writer.Write();window.Finalize()
            canvas=Image.new('RGB',(1400,1060),(244,243,240));canvas.paste(Image.open(variant/(view+'.render.png')).convert('RGB'),(0,100))
            draw=ImageDraw.Draw(canvas);font=ImageFont.truetype(str(font_path),30);small=ImageFont.truetype(str(font_path),20)
            draw.text((35,20),f'Paramak ordinary tokamak / {name} / {view}',fill='#242b31',font=font)
            draw.text((35,63),f'180-degree sector | elongation {elongation:g} | coordinates in metres, Z up',fill='#4e555b',font=small)
            for i,component in enumerate(NAMES):
                x=40+i*220;draw.rectangle((x,964,x+23,987),fill=COLORS[i]);draw.text((x+33,962),component,fill='#242b31',font=small)
            draw.text((35,1010),'CAD identity colors; materials unknown. No equilibrium, solver result or physical validation.',fill='#4e555b',font=small)
            canvas.save(variant/(view+'.png'))
        checks={
            'adaptive_volume_convergence':all(c['volume_measurement']['relative_convergence']<=TOL['adaptive_volume_relative_convergence'] for c in records),
            'native_topology_positive_volumes':all(c['valid'] and c['solid_count']==1 and c['volume_m3']>0 for c in records),
            'component_mapping':list(components)==NAMES,
            'source_dimensions':bool(np.max(abs(actual_dims-expected_dims))<=TOL['dimensional_m']),
            'half_sector_y_nonnegative':bool(physical_bounds[0,1]>=-TOL['dimensional_m']),
            'z_symmetry':bool(abs(physical_bounds[0,2]+physical_bounds[1,2])<TOL['dimensional_m']),
            'pairwise_no_unintended_overlap':all(not p['unintended_overlap'] for p in pairs),
            'intended_contacts_observed':all(p['observed_contact'] for p in pairs if p['intended_contact']),
            'plasma_shell_clearance':next(p['minimum_distance_m'] for p in pairs if {p['a'],p['b']}=={'layer_3','plasma'})>=.6-TOL['plasma_clearance_m'],
            'component_step_roundtrip':all(c['step_roundtrip']['valid'] and c['step_roundtrip']['solid_count']==1 and c['step_roundtrip']['maximum_bound_error_m']<=TOL['roundtrip_bound_m'] and c['step_roundtrip']['relative_volume_error']<=TOL['roundtrip_relative_volume'] for c in records),
            'corrected_assembly_step_roundtrip':corrected_import.isValid() and len(corrected_import.Solids())==6 and bool(abs(np.array(bounds(corrected_import,.001))-physical_bounds).max()<=TOL['roundtrip_bound_m']),
            'display_engineering_bounds_volumes':all(c['display']['maximum_bound_error_m']<=TOL['display_bound_m'] and c['display']['relative_volume_error']<=TOL['display_relative_volume'] for c in records),
            'display_topology':all(c['display']['watertight'] and c['display']['winding_consistent'] and c['display']['positive_volume'] for c in records),
            'display_roundtrip':exported_names==sorted(NAMES) and display_roundtrip['maximum_bound_error_m']<=TOL['display_export_bound_m'],
        }
        result={'variant':name,'variant_hash':variant_hash,'elongation':elongation,'executed':True,'elapsed_seconds':time.monotonic()-start,
            'entrypoint':str(entrypoint),'input_identity':input_identity,'bounds_m':physical_bounds.tolist(),'dimensions_m':actual_dims.tolist(),'expected_dimensions_m':expected_dims.tolist(),
            'components':records,'pairs':pairs,'tolerances':TOL,'measurement_methods':{'bounds':'OCP BRepBndLib.AddOptimal(useTriangulation=False,useShapeTolerance=False)','volumes':'Adaptive OCP BRepGProp.VolumePropertiesGK(Eps=1e-9), checked against 1e-7'},'checks':checks,'all_geometric_checks_passed':all(checks.values()),
            'raw_step':{'status':'failed_physical_units','header_declares':'mm','coordinate_meaning':'cm','raw_import_physical_dimensions_m':(np.diff(np.array(bounds(raw_import,.001)),axis=0)[0]).tolist(),'raw_size_is_one_tenth_intended':True},
            'display_roundtrip':display_roundtrip,'images_reviewed':False,'analysis_readiness':'not_prepared','physical_validation':'not_assessed'}
        write(variant/'checks.json',result); write(reports/(name+'-checks.json'),result)
        results.append(result)
        print(f'{name}: {checks}',flush=True)
    comparison={'model_record_id':MODEL_ID,'baseline_variant_hash':results[0]['variant_hash'],'edited_variant_hash':results[1]['variant_hash'],
        'edit':{'parameter':'elongation','original':2,'edited':1.8,'unit':'dimensionless','accepted_discrete_values':[1.8,2.0],
                'continuous_interval_verified':False,'physical_feasibility_bounds':{'min':None,'max':None}},
        'component_volume_changes_m3':[{ 'id':a['id'],'baseline':a['volume_m3'],'variant':b['volume_m3'],'difference':b['volume_m3']-a['volume_m3']} for a,b in zip(results[0]['components'],results[1]['components'])]}
    comparison['plasma_volume_ratio'] = results[1]['components'][-1]['volume_m3']/results[0]['components'][-1]['volume_m3']
    comparison['plasma_display_volume_ratio'] = results[1]['components'][-1]['display']['volume_m3']/results[0]['components'][-1]['display']['volume_m3']
    comparison['expected_plasma_volume_ratio'] = .9
    comparison['plasma_ratio_relative_tolerance'] = 1e-5
    comparison['plasma_geometric_scaling_passed'] = abs(comparison['plasma_volume_ratio']/.9-1)<=1e-5
    write(reports/'comparison.json',comparison)
    manifest={'schema_version':'fusion-r6a-artifacts/1','model_record_id':MODEL_ID,'original_model_sha256':MODEL_SHA,
        'executed_at':datetime.now(timezone.utc).isoformat(),'command':sys.argv,'tool_sha256':digest(__file__),
        'input_verification':{'status':'passed','model_sha256':MODEL_SHA,'scope':'Bundled source hashes and accepted original recipe'},
        'rights':{'status':'approved_for_intended_use','license':'MIT','notice_path':'research/fusion/reproductions/r6a-paramak/NOTICE.txt','scope':'Generated educational display derivatives and reproduction reports, retaining MIT notice and attribution.'},
        'units':{'source':'cm','canonical':'m','engineering_step':'mm','source_to_canonical':.01,'source_to_corrected_step':10,'display_up_axis':'Z','display_origin':[0,0,0],'display_orientation_note':'GLB stores source Z-up coordinates. App must rotate -90 degrees around X to use Three.js Y-up; no additional scale.'},
        'tessellation':{'engine':'CadQuery Shape.tessellate','relative_deflection':.0002,'angular_tolerance_radian':.025,'acceptance':'Measured per-component bounds within 3 mm and volume within 0.3% of engineering CAD; not a certified Hausdorff or simulation mesh check.'},
        'variants':[],'records':[],'independent_backup_verified':False,'remote_retrieval_uri':None}
    for r in results:
        v=r['variant']
        manifest['variants'].append({'id':v,'variant_hash':r['variant_hash'],'display_state':'pending_visual_review' if r['all_geometric_checks_passed'] else 'unavailable_failed_checks',
                                    'display_path':str(out/v/'display-m-zup.glb'),'display_sha256':digest(out/v/'display-m-zup.glb'),'checks_path':f'reports/{v}-checks.json'})
    for path in sorted(out.rglob('*')):
        if path.is_file() and 'matplotlib-cache' not in path.parts:
            rel=path.relative_to(out).as_posix()
            role='display_derivative' if path.suffix=='.glb' else 'review_image' if path.suffix=='.png' else 'engineering_derivative' if path.suffix=='.step' else 'run_evidence'
            manifest['records'].append({'relative_path':rel,'local_path':str(path),'size_bytes':path.stat().st_size,'sha256':digest(path),'role':role,'generated_this_run':True,'raw_physical_units_failed':path.name=='tokamak_minimal.step'})
    write(reports/'artifact-manifest.json',manifest)
    print(json.dumps({'reports':str(reports),'outputs':str(out),'geometry_passed':all(r['all_geometric_checks_passed'] for r in results)}),flush=True)

if __name__ == '__main__':
    main()
