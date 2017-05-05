import requests
import sys
from flask import Flask, abort, jsonify
from flask_cors import CORS, cross_origin
app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

@app.route("/getTargetNames/<source>")
@cross_origin()
def get_target_names(source):
    solr_url = "http://localhost:8983/solr/docsdev/query?q=type:target AND source:" \
               + source + \
               "&rows=2147483647&wt=json"
    solr_return = requests.get(solr_url).json()

    #valid returned JSON
    if not "response" in solr_return:
        raise Exception("The returned list does not contain response attribute")

    if not "docs" in solr_return["response"]:
        raise Exception("Response attrbute does not contain docs sub-attribute")

    solr_docs = solr_return["response"]["docs"]

    #construct the response in the same format as postgres DB
    return_dict = {};
    return_dict["target_name"] = [];
    for doc in solr_docs:
        if "can_name" not in doc:
            continue

        return_dict["target_name"].append({
            0: doc["can_name"]
        })

    return jsonify(return_dict)

@app.route("/getElementNames/<source>")
@cross_origin()
def get_element_names(source):
    solr_url = "http://localhost:8983/solr/docsdev/query?q=type:element AND source:" \
               + source + \
               "&rows=2147483647&wt=json"
    solr_return = requests.get(solr_url).json()

    # valid returned JSON
    if not "response" in solr_return:
        raise Exception("The returned list does not contain response attribute")

    if not "docs" in solr_return["response"]:
        raise Exception("Response attrbute does not contain docs sub-attribute")

    solr_docs = solr_return["response"]["docs"]

    # construct the response in the same format as postgres DB
    return_dict = {};
    return_dict["results"] = [];
    for doc in solr_docs:
        if "can_name" not in doc:
            continue

        return_dict["results"].append({
            0: doc["can_name"],
            1: "Element"
        })

    return jsonify(return_dict)

@app.route("/getMineralNames/<source>")
@cross_origin()
def get_mineral_names(source):
    solr_url = "http://localhost:8983/solrdev/docs/query?q=type:mineral AND source:" \
               + source + \
               "&rows=2147483647&wt=json"
    solr_return = requests.get(solr_url).json()

    # valid returned JSON
    if not "response" in solr_return:
        raise Exception("The returned list does not contain response attribute")

    if not "docs" in solr_return["response"]:
        raise Exception("Response attrbute does not contain docs sub-attribute")

    solr_docs = solr_return["response"]["docs"]

    # construct the response in the same format as postgres DB
    return_dict = {};
    return_dict["results"] = [];
    for doc in solr_docs:
        if "name" not in doc:
            continue

        return_dict["results"].append({
            0: doc["name"],
            1: "Mineral"
        })

    return jsonify(return_dict)

@app.route("/getPrimaryAuthorNames")
@cross_origin()
def get_primary_author_names():
    solr_url = "http://localhost:8983/solr/docsdev/query?q=type:doc&fl=primaryauthor&" \
               "rows=2147483647&wt=json"
    solr_return = requests.get(solr_url).json()

    # valid returned JSON
    if not "response" in solr_return:
        raise Exception("The returned list does not contain response attribute")

    if not "docs" in solr_return["response"]:
        raise Exception("Response attrbute does not contain docs sub-attribute")

    solr_docs = solr_return["response"]["docs"]

    # construct the response in the same format as postgres DB
    return_dict = {};
    return_dict["primary_author"] = [];
    for doc in solr_docs:
        if "primaryauthor" not in doc:
            continue

        return_dict["primary_author"].append({
            0: doc["primaryauthor"],
        })

    return jsonify(return_dict)

@app.route("/getStatistics/<source>")
@cross_origin()
def get_statistics(source):
    statistics = {}
 
    #get documents count
    solr_doc_url = "http://localhost:8983/solr/docsdev/query?q=type:doc&rows=0"
    solr_doc_return = requests.get(solr_doc_url).json()
    if not "response" in solr_doc_return:
        raise Exception("The returned list dors not contain response field")
    if not "numFound" in solr_doc_return["response"]:
        raise Exception("response field does not contain numFound sub-attribtue")
    solr_docs = solr_doc_return["response"]["numFound"]
    statistics["document_count"] = {
        0: {0: solr_docs}
    }

    #get target count
    solr_target_url = "http://localhost:8983/solr/docsdev/query?q=source:" + source + "&fq=type:target&rows=0&facet=true&facet.field=name&facet.mincount=1&facet.limit=65535"
    solr_target_return = requests.get(solr_target_url).json()
    solr_targets = solr_target_return["facet_counts"]["facet_fields"]["name"]
    statistics["target_count"] = {
        0: {0: len(solr_targets) / 2}
    }

    #get element count 
    solr_element_url = "http://localhost:8983/solr/docsdev/query?q=source:" + source + "&fq=type:element&rows=0&facet=true&facet.field=name&facet.mincount=1&facet.limit=65535"
    solr_element_return = requests.get(solr_element_url).json()
    solr_elements = solr_element_return["facet_counts"]["facet_fields"]["name"]
    statistics["element_count"] = {
        0: {0: len(solr_elements) / 2}
    }

    # get feature count
    solr_feature_url = "http://localhost:8983/solr/docsdev/query?q=source:" + source + "&fq=type:feature&rows=0&facet=true&facet.field=name&facet.mincount=1&facet.limit=65535"
    solr_feature_return = requests.get(solr_feature_url).json()
    solr_features = solr_feature_return["facet_counts"]["facet_fields"]["name"]
    statistics["feature_count"] = {
        0: {0: len(solr_features) / 2}
    }

    # get material count
    solr_material_url = "http://localhost:8983/solr/docsdev/query?q=source:" + source + "&fq=type:material&rows=0&facet=true&facet.field=name&facet.mincount=1&facet.limit=65535"
    solr_material_return = requests.get(solr_material_url).json()
    solr_materials = solr_material_return["facet_counts"]["facet_fields"]["name"]
    statistics["material_count"] = {
        0: {0: len(solr_materials) / 2}
    }
 
    # get mineral count
    solr_mineral_url = "http://localhost:8983/solr/docsdev/query?q=source:" + source + "&fq=type:mineral&rows=0&facet=true&facet.field=name&facet.mincount=1&facet.limit=65535"
    solr_mineral_return = requests.get(solr_mineral_url).json()
    solr_minerals = solr_mineral_return["facet_counts"]["facet_fields"]["name"]
    statistics["mineral_count"] = {
        0: {0: len(solr_minerals) / 2}
    }
   
    # get relation count
    solr_relation_url = "http://localhost:8983/solr/docsdev/query?q=source:" + source + "&rows=0&fq=mainType:event"
    solr_relation_return = requests.get(solr_relation_url).json()
    solr_relations = solr_relation_return["response"]["numFound"]
    statistics["event_count"] = {
        0: {0: solr_relations}
    }
    return jsonify(statistics)

@app.route("/getResultsBySearchStr/<source>/<searchStr>")
@cross_origin()
def get_results_by_searchStr(source, searchStr):
    #store target names searched by searchStr.
    #searchStr can be:
    # 1. target name
    # 2. componment name (element name or mineral name)
    # 3. primary author name
    target_names = [];
    #store the search results that are returned to web
    #note that return_dict needs to be consistent with postgres DB
    results = []
    return_dict = {}

    #searchStr = target name case
    solr_target = "http://localhost:8983/solr/docsdev/query?q=target_names_tios:\"" \
                  + searchStr + \
                  "\"&fq=source:" \
                  + source + \
                  "&facet=true&facet.field=target_names_ss&rows=0&facet.mincount=1" \
                  "&facet.limit=65535&wt=json"
    solr_return = requests.get(solr_target).json()
    # valid returned JSON
    if not "facet_counts" in solr_return:
        raise Exception("The returned list does not contain facet_counts attribute")
    if not "facet_fields" in solr_return["facet_counts"]:
        raise Exception("facet_counts attrbute does not contain facet_fields sub-attribute")
    if not "target_names_ss" in solr_return["facet_counts"]["facet_fields"]:
        raise Exception("facet_fields attrbute does not contain target_names_ss sub-attribute")
    #Targets returned sometimes is a list. E.g. ["windjana", "stephen"] is retrieved when search
    # windjana, but we only need windjana. We process the returned list from ["windjana", "stephen"]
    # into just ["windjana"]. We get a list of targets when we search by target name, and then we
    # do a string match to remove un-needed targets.
    solr_target_names = solr_return["facet_counts"]["facet_fields"]["target_names_ss"]
    #step 1: remove integer counts first
    solr_target_names_no_integer = [target for target in solr_target_names if not isinstance(target, int)]
    #step 2: string match to remove un-needed targets
    solr_target_names_remove = [target for target in solr_target_names_no_integer
                                if searchStr.lower() == target.lower()]
    target_names.extend(solr_target_names_remove)
    print target_names

    #searchStr = conponment name case
    #Get target names by searching conponent name
    solr_target_by_component = "http://localhost:8983/solr/docsdev/query?q=cont_names_tios:\""\
                               + searchStr + \
                               "\"&fq=source:" \
                               + source + \
                               "&facet=true&facet.field=target_names_ss&rows=0&facet.mincount=1" \
                               "&facet.limit=65535&wt=json"
    solr_return = requests.get(solr_target_by_component).json()
    # valid returned JSON
    if not "facet_counts" in solr_return:
        raise Exception("The returned list does not contain facet_counts attribute")
    if not "facet_fields" in solr_return["facet_counts"]:
        raise Exception("facet_counts attrbute does not contain facet_fields sub-attribute")
    if not "target_names_ss" in solr_return["facet_counts"]["facet_fields"]:
        raise Exception("facet_fields attrbute does not contain target_names_ss sub-attribute")
    #Targets name in ["windjana", 3, "big sky", 2, ...] format
    #Process it into ["windjana", "big sky", ...] format
    solr_target_names = solr_return["facet_counts"]["facet_fields"]["target_names_ss"]
    #rempve integer counts
    solr_target_names_no_integer = [target for target in solr_target_names if not isinstance(target, int)]
    target_names.extend(solr_target_names_no_integer)

    #searchStr = primary author name case
    solr_target_by_primaryauthor = "http://localhost:8983/solr/docsdev/query?q={!join+from=id+to=p_id}primaryauthor:\"" \
                                   + searchStr + \
                                   "\"&fq=source:" \
                                   + source + \
                                   " AND type:contains&facet=true&facet.field=target_names_ss&rows=0&facet.mincount=1" \
                                   "&facet.limit=65535&wt=json"
    solr_return = requests.get(solr_target_by_primaryauthor).json()
    # valid returned JSON
    if not "facet_counts" in solr_return:
        raise Exception("The returned list does not contain facet_counts attribute")
    if not "facet_fields" in solr_return["facet_counts"]:
        raise Exception("facet_counts attrbute does not contain facet_fields sub-attribute")
    if not "target_names_ss" in solr_return["facet_counts"]["facet_fields"]:
        raise Exception("facet_fields attrbute does not contain target_names_ss sub-attribute")
    # Targets name in ["windjana", 3, "big sky", 2, ...] format
    # Process it into ["windjana", "big sky", ...] format
    solr_target_names = solr_return["facet_counts"]["facet_fields"]["target_names_ss"]
    # rempve integer counts
    solr_target_names_no_integer = [target for target in solr_target_names if not isinstance(target, int)]
    target_names.extend(solr_target_names_no_integer)

    for target_name in target_names:
        solr_contains = "http://localhost:8983/solr/docsdev/query?q=target_names_tios:\"" + target_name + "\"&source:" + source + "&rows=65535&wt=json"
        solr_return = requests.get(solr_contains).json()
        if not "response" in solr_return:
            raise Exception("The returned list does not contain response attribute")
        if not "docs" in solr_return["response"]:
            raise Exception("response attribute does not contain docs sub-attribute")
        solr_docs = solr_return["response"]["docs"]
        for doc in solr_docs:
            if not "cont_names_ss" in doc:
                break
            if not "cont_ids_ss" in doc:
                break
            components = doc["cont_names_ss"]
            component_ids = doc["cont_ids_ss"]
            if not len(components) == len(component_ids):
                break
            for idx, component in enumerate(components):
                component_type_url = "http://localhost:8983/solr/docsdev/query?q=id:" + component_ids[idx] + "&rows=65535&wt=json"
                component_type_return = requests.get(component_type_url).json()
                component_type_docs = component_type_return["response"]["docs"]
                for component_type_doc in component_type_docs:
                    component_type = component_type_doc["type"]

                solr_documents = "http://localhost:8983/solr/docsdev/query?q=type:doc&fq=id:" \
                                 + doc["p_id"] + \
                                 "&fl=primaryauthor,title,year,venue,url&wt=json"
                solr_return_info = requests.get(solr_documents).json()
                if not "response" in solr_return_info:
                    raise Exception("The returned list does not contain response attribute")
                if not "docs" in solr_return_info["response"]:
                    raise Exception("response attribute does not contain docs sub-attribute")
                solr_docs_info = solr_return_info["response"]["docs"]
                for doc_info in solr_docs_info:
                    if not "primaryauthor" in doc_info:
                        doc_info["primaryauthor"] = "Undefined"
                    if not "title" in doc_info:
                        doc_info["title"] = "Undefined"
                    if not "year" in doc_info:
                        doc_info["year"] = "Undefined"
                    if not "venue" in doc_info:
                        doc_info["venue"] = "Undefined"
                    if not "url" in doc_info:
                        doc_info["url"] = "Undefined"
                    results.append([target_name, "", "", component, component_type, doc_info["primaryauthor"],
                                    doc_info["title"], doc["excerpt_t"], doc_info["year"], doc_info["venue"],
                                    doc_info["url"]])
    return_dict["results"] = results

    return jsonify(return_dict)

if __name__ == "__main__":
    app.run()
