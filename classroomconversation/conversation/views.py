import json
import uuid
import xml.etree.ElementTree as ElementTree

from django.shortcuts import render, redirect
from django.core.files import File

from .forms import ConversationForm
from .models import Conversation


def upload_document(request):
    if request.method == "POST":
        form = ConversationForm(request.POST, request.FILES)

        if form.is_valid():
            conversation = form.save(commit=False)
            conversation.uuid = str(uuid.uuid4())
            conversation.json = graphml_to_json(File(conversation.document))
            conversation.save()
            return redirect("document_list")

    form = ConversationForm()
    return render(request, "upload_document.html", {"form": form})


def document_list(request):
    conversations = Conversation.objects.all().order_by("-created")
    return render(request, "document_list.html", {"conversations": conversations})


#### HELPES ####


def graphml_to_json(file):
    graphml = {
        "graph": "{http://graphml.graphdrawing.org/xmlns}graph",
        "node": "{http://graphml.graphdrawing.org/xmlns}node",
        "edge": "{http://graphml.graphdrawing.org/xmlns}edge",
        "data": "{http://graphml.graphdrawing.org/xmlns}data",
        "shapenode": "{http://www.yworks.com/xml/graphml}ShapeNode",
        "geometry": "{http://www.yworks.com/xml/graphml}Geometry",
        "fill": "{http://www.yworks.com/xml/graphml}Fill",
        "boderstyle": "{http://www.yworks.com/xml/graphml}BorderStyle",
        "nodelabel": "{http://www.yworks.com/xml/graphml}NodeLabel",
        "shape": "{http://www.yworks.com/xml/graphml}Shape",
        "line": "{http://www.yworks.com/xml/graphml}PolyLineEdge",
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
    edges = graph.findall(graphml.get("edge"))
    out = {"nodes": {}, "edges": []}

    for node in nodes:
        data = node.find(graphml.get("data"))
        shapenode = data.find(graphml.get("shapenode"))

        if shapenode:
            nodelabel = shapenode.find(graphml.get("nodelabel"))
            shape = shapenode.find(graphml.get("shape"))

            out["nodes"][node.get("id")] = {
                "shape": shape.get("type"),
                "label": nodelabel.text if nodelabel else "",
            }

    for edge in edges:
        data = edge.find(graphml.get("data"))
        line = data.find(graphml.get("line"))
        label = (
            line.find(graphml.get("edgelabel")).text
            if line and line.find(graphml.get("edgelabel"))
            else ""
        )

        out["edges"].append(
            {
                "id": edge.get("id"),
                "source": edge.get("source"),
                "target": edge.get("target"),
                "percentage": float(label) if label else 0,
            }
        )

    return json.dumps(out, ensure_ascii=False)
