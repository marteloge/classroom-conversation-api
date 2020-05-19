import uuid
import xml.etree.ElementTree as ElementTree

from rest_framework.permissions import AllowAny
from rest_framework import viewsets

from django.shortcuts import render, redirect
from django.core.files import File

from .forms import ConversationForm
from .models import Conversation
from .serializers import ConversationSerializer

### API ###
class ConversationDetailAPIView(viewsets.ReadOnlyModelViewSet):
    queryset = Conversation.objects.all()
    serializer_class = ConversationSerializer
    permission_classes = [AllowAny]
    lookup_field = "uuid"


### FILE UPLOADER ###
def upload_document(request):
    if request.method == "POST":
        form = ConversationForm(request.POST, request.FILES)

        if form.is_valid():
            conversation = form.save(commit=False)
            conversation.uuid = str(uuid.uuid4())
            conversation.json = graphml_to_json(
                File(conversation.document), conversation.uniform_probability
            )
            conversation.save()
            return redirect("document_list")

    form = ConversationForm()
    return render(request, "upload_document.html", {"form": form})


def document_list(request):
    conversations = Conversation.objects.all().order_by("-created")
    return render(request, "document_list.html", {"conversations": conversations})


#### HELPES ####


def graphml_to_json(file, uniformProbability):
    graphml = {
        "graph": "{http://graphml.graphdrawing.org/xmlns}graph",
        "key": "{http://graphml.graphdrawing.org/xmlns}key",
        "node": "{http://graphml.graphdrawing.org/xmlns}node",
        "edge": "{http://graphml.graphdrawing.org/xmlns}edge",
        "data": "{http://graphml.graphdrawing.org/xmlns}data",
        "shapenode": "{http://www.yworks.com/xml/graphml}ShapeNode",
        "geometry": "{http://www.yworks.com/xml/graphml}Geometry",
        "fill": "{http://www.yworks.com/xml/graphml}Fill",
        "boderstyle": "{http://www.yworks.com/xml/graphml}BorderStyle",
        "nodelabel": "{http://www.yworks.com/xml/graphml}NodeLabel",
        "shape": "{http://www.yworks.com/xml/graphml}Shape",
        "polyLine": "{http://www.yworks.com/xml/graphml}PolyLineEdge",
        "arrow": "{http://www.yworks.com/xml/graphml}Arrows",
        "bendStyle": "{http://www.yworks.com/xml/graphml}BendStyle",
        "path": "{http://www.yworks.com/xml/graphml}Path",
        "linestyle": "{http://www.yworks.com/xml/graphml}LineStyle",
        "edgelabel": "{http://www.yworks.com/xml/graphml}EdgeLabel",
    }

    file.seek(0)
    tree = ElementTree.parse(file)

    root = tree.getroot()
    graph = root.find(graphml.get("graph"))
    nodes = graph.findall(graphml.get("node"))
    out = {
        "uniformProbability": uniformProbability,
        "start": "",
        "end": "",
        "question": {},
        "answer": {},
    }

    ## node kan have different data elements.
    nodeDataKeyId = ""

    for key in root.findall(graphml.get("key")):
        if key.get("yfiles.type") and key.get("yfiles.type") == "nodegraphics":
            nodeDataKeyId = key.get("id")

    for node in nodes:
        nodeid = node.get("id")
        data = node.find(graphml.get("data") + "[@key='" + nodeDataKeyId + "']")
        shapenode = data.find(graphml.get("shapenode"))

        if shapenode:
            shape = shapenode.find(graphml.get("shape")).get("type")
            nodelabel = shapenode.find(graphml.get("nodelabel"))

            node_edges = graph.findall(
                graphml.get("edge") + "[@source='" + str(nodeid) + "']"
            )

            if shape == "roundrectangle":
                answers = []
                for edge in node_edges:
                    target_id = edge.get("target")
                    edgedata = edge.find(graphml.get("data"))
                    line = edgedata.find(graphml.get("polyLine"))
                    edgelabel = None

                    if line:
                        edgelabel = line.find(graphml.get("edgelabel"))

                    if not uniformProbability and edgelabel and edgelabel.text:
                        try:
                            answers.append(
                                {"id": target_id, "probability": float(edgelabel.text)}
                            )
                        except ValueError:
                            pass
                    else:
                        answers.append({"id": target_id})

                out["question"][nodeid] = {
                    "id": nodeid,
                    "shape": shape,
                    "label": nodelabel.text if nodelabel else "",
                    "answers": answers,
                }
            elif shape == "diamond":
                alternatives = [edge.get("target") for edge in node_edges]

                out["answer"][nodeid] = {
                    "id": nodeid,
                    "shape": shape,
                    "label": nodelabel.text if nodelabel else "",
                    "alternatives": alternatives,
                }
            elif "star" in str(shape):
                out["start"] = {
                    "id": nodeid,
                    "label": nodelabel.text if nodelabel else "",
                    "type": shape,
                    "firstQuestion": node_edges[0].get("target"),
                }
            elif shape == "octagon":
                out["end"] = nodeid
    return out
