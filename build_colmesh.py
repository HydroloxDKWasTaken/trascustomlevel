# build_colmesh.py mesh.obj mesh.colmeshtxt
# Creates a mkloadob file with the cdc::Mesh of mesh.obj
# In Blender: Export > Wavefront (.obj)
# Check "Triangulated Mesh", and turn everything else off
# Also set "Forward Axis" to "Y"
# And "Up Axis" to "Z" (needed because CDC is Z-up)
# You may want to check "Include Selection Only" if you have multiple objects
# in your scene, but only want to export one.
import sys

def build_colmesh(src, dest):
    min_verts = [99999.0, 99999.0, 99999.0]
    max_verts = [-99999.0, -99999.0, -99999.0]
    verts = []
    faces = []
    faces_usagecount = dict()

    def get_normal(v0, v1, v2):
        ret = [0.0, 0.0, 0.0]
        ret[0] = (v2[2] - v0[2]) * (v1[1] - v0[1]) - (v2[1] - v0[1]) * (v1[2] - v0[2])
        ret[1] = (v2[0] - v0[0]) * (v1[2] - v0[2]) - (v2[2] - v0[2]) * (v1[0] - v0[0])
        ret[2] = (v2[1] - v0[1]) * (v1[0] - v0[0]) - (v2[0] - v0[0]) * (v1[1] - v0[1])
        return ret

    with open(src, "r") as f:
        for line in f:
            data = line.split()
            # v -10.000000 -0.547828 10.000000
            if data[0] == "v":
                x = float(data[1])
                y = float(data[2])
                z = float(data[3])
                if x < min_verts[0]:
                    min_verts[0] = x
                if y < min_verts[1]:
                    min_verts[1] = y
                if z < min_verts[2]:
                    min_verts[2] = z
                if x > max_verts[0]:
                    max_verts[0] = x
                if y > max_verts[1]:
                    max_verts[1] = y
                if z > max_verts[2]:
                    max_verts[2] = z
                verts.append((x, y, z))
            elif data[0] == "f":
                for i in range(1, len(data)):
                    data[i] = data[i].split("/")[0]
                v0 = int(data[1]) - 1
                v1 = int(data[2]) - 1
                v2 = int(data[3]) - 1
                # Note the -1 here! OBJ indices start at 1 for god knows what reason
                faces.append((v0, v1, v2))
                if v0 not in faces_usagecount:
                    faces_usagecount[v0] = 0
                if v1 not in faces_usagecount:
                    faces_usagecount[v1] = 0
                if v2 not in faces_usagecount:
                    faces_usagecount[v2] = 0
                faces_usagecount[v0] += 1
                faces_usagecount[v1] += 1
                faces_usagecount[v2] += 1

    with open(dest, "w") as f:
        f.write("[mesh]\n")
        f.write("; cdc::BBox m_box\n")
        f.write("; {\n")
        f.write("    float32={} {} {} 0.0 ; cdc::Vector3 bMin\n".format(min_verts[0], min_verts[1], min_verts[2]))
        f.write("    float32={} {} {} 0.0 ; cdc::Vector3 bMax\n".format(max_verts[0], max_verts[1], max_verts[2]))
        f.write("; }\n")
        f.write("ptr=verts ; void* m_vertices\n")
        f.write("ptr=faces ; cdc::IndexedFace* m_faces\n")
        f.write("ptr=dummyaabb ; cdc::AABBNode* m_root\n")
        f.write("uint32=1 ; unsigned int m_numNodes\n")
        f.write("uint32={} ; unsigned int m_numFaces\n".format(len(faces)))
        f.write("uint32={} ; unsigned int m_numVertices\n".format(len(verts)))
        f.write("uint32=0 ; unsigned int m_numDegenerateFaces\n")
        f.write("uint32=0 ; unsigned int m_numNonManifoldEdges\n")
        f.write("; cdc::Mesh::VertexType::VERTEX_FLOAT32\n")
        f.write("uint16=1 ; unsigned short m_vertexType\n")
        f.write("uint16={} ; unsigned short m_height\n".format(round(max_verts[1] - min_verts[1])))
        f.write("pad=12\n")
        f.write("\n")
        f.write("[dummyaabb]\n")
        f.write("float32={} {} {} ; float m_min[3]\n".format(min_verts[0], min_verts[1], min_verts[2]))
        f.write("float32={} {} {} ; float m_max[3]\n".format(max_verts[0], max_verts[1], max_verts[2]))
        f.write("; bitfield\n")
        f.write("; {\n")
        f.write("; unsigned int m_numFaces : 8\n")
        f.write("; unsigned int m_index : 24\n")
        if len(faces) > 255:
            sys.exit(1)
        raw_uint = 0
        raw_uint |= len(faces)
        f.write("; NOTE: zero means leaf\n")
        f.write("uint32={}\n".format(raw_uint))
        f.write("; }\n")
        f.write("[verts]\n")
        for v in verts:
            f.write("float32={} {} {}\n".format(v[0], v[1], v[2]))
        f.write("\n")
        f.write("[faces]\n")
        for fa in faces:
            f.write("uint32={} ; unsigned int i0\n".format(fa[0]))
            f.write("uint32={} ; unsigned int i1\n".format(fa[1]))
            f.write("uint32={} ; unsigned int i2\n".format(fa[2]))
            # This makes collision ""works"" (but it seems reversed)
            # f.write("uint32={} ; unsigned int i0\n".format(fa[0]))
            # f.write("uint32={} ; unsigned int i1\n".format(fa[2]))
            # f.write("uint32={} ; unsigned int i2\n".format(fa[1]))
            # This makes collision ""works"" (but it seems reversed)
            # f.write("uint32={} ; unsigned int i0\n".format(fa[1]))
            # f.write("uint32={} ; unsigned int i1\n".format(fa[0]))
            # f.write("uint32={} ; unsigned int i2\n".format(fa[2]))
            print(get_normal(verts[fa[0]], verts[fa[1]], verts[fa[2]]))
            # f.write("uint32={} ; unsigned int i0\n".format(fa[1]))
            # f.write("uint32={} ; unsigned int i1\n".format(fa[2]))
            # f.write("uint32={} ; unsigned int i2\n".format(fa[0]))
            # f.write("uint32={} ; unsigned int i0\n".format(fa[2]))
            # f.write("uint32={} ; unsigned int i1\n".format(fa[1]))
            # f.write("uint32={} ; unsigned int i2\n".format(fa[0]))
            # f.write("uint32={} ; unsigned int i0\n".format(fa[2]))
            # f.write("uint32={} ; unsigned int i1\n".format(fa[0]))
            # f.write("uint32={} ; unsigned int i2\n".format(fa[1]))
            adjacency_flags = 0
            if faces_usagecount[fa[0]] > 1:
                adjacency_flags |= 1 # CHECK_VERT0
            if faces_usagecount[fa[1]] > 1:
                adjacency_flags |= 2 # CHECK_VERT1
            if faces_usagecount[fa[2]] > 1:
                adjacency_flags |= 4 # CHECK_VERT2
            f.write("uint8={} ; unsigned char adjacencyFlags\n".format(adjacency_flags))
            f.write("; NOTE: the game will skip this tri if (collisionFlags & wantedFlags) == 0\n")
            # 3 is used for... something. idk i just copied this from container1
            f.write("uint8=3 ; unsigned char collisionFlags\n")
            f.write("; NOTE: 0x200 is flooring... i think\n")
            f.write("uint16=0xA0 ; unsigned short clientFlags\n")
            f.write("uint32=0 ; unsigned int materialType\n")

