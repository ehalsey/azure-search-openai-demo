import openai
from approaches.approach import Approach
from azure.search.documents import SearchClient
from azure.search.documents.models import QueryType
from text import nonewlines

# Simple retrieve-then-read implementation, using the Cognitive Search and OpenAI APIs directly. It first retrieves
# top documents from search, then constructs a prompt with them, and then uses OpenAI to generate an completion 
# (answer) with that prompt.
class RetrieveThenReadApproach(Approach):

    template = \
"You are a Microsoft Solution Architect who is an expert in Intelligent Document Processing helping NathCorp employees respond to a request for proposal. " \
"Answer the question first using the data provided in the information sources below. If an answer cannot be found in the data provided you can use other sources." \
"For tabular information return it as an html table. Do not return markdown format. "  + \
"Each source has a name followed by colon and the actual information, always include the source name for each fact you use in the response. " + \
"If you cannot answer, say you don't know. " + \
"Company names other than NathCorp should be replaced with 'client'. " + \
"""

###
Question: 'How does the proposed solution help automate content discovery and categorization within an organization?'

Sources:
info1.txt: The proposed solution uses Microsoft Syntex to automate content discovery and categorization.
info2.pdf: Microsoft AI Builder can auto-classify and auto-categorize documents.
info3.pdf: Azure Cognitive Services will be used automate content discovery and categorization.
info4.pdf: Microsoft Syntex uses AI to automatically classify, extract, and process information from documents, reducing the need for manual data entry.

Answer:
The proposed solution leverages SharePoint Online, Microsoft Syntex[info1.txt], and Azure Cognitive Services[info4.txt] to automate content discovery and categorization. SharePoint Online serves as the backbone for document management, providing a platform to store, share, and collaborate on content. Microsoft Syntex uses AI to automatically classify, extract, and process information from documents, reducing the need for manual data entry. Azure Cognitive Services and Azure Cognitive Search enable advanced search capabilities, using AI to understand natural language queries and surface relevant content. Together, these technologies provide a comprehensive, automated system for content discovery and categorization within an organization[info3.txt].

###
Question: '{q}'?

Sources:
{retrieved}

Answer:
"""

    def __init__(self, search_client: SearchClient, openai_deployment: str, sourcepage_field: str, content_field: str):
        self.search_client = search_client
        self.openai_deployment = openai_deployment
        self.sourcepage_field = sourcepage_field
        self.content_field = content_field

    def run(self, q: str, overrides: dict) -> any:
        use_semantic_captions = True if overrides.get("semantic_captions") else False
        top = overrides.get("top") or 3
        exclude_category = overrides.get("exclude_category") or None
        filter = "category ne '{}'".format(exclude_category.replace("'", "''")) if exclude_category else None

        if overrides.get("semantic_ranker"):
            r = self.search_client.search(q, 
                                          filter=filter,
                                          query_type=QueryType.SEMANTIC, 
                                          query_language="en-us", 
                                          query_speller="lexicon", 
                                          semantic_configuration_name="default", 
                                          top=top, 
                                          query_caption="extractive|highlight-false" if use_semantic_captions else None)
        else:
            r = self.search_client.search(q, filter=filter, top=top)
        if use_semantic_captions:
            results = [doc[self.sourcepage_field] + ": " + nonewlines(" . ".join([c.text for c in doc['@search.captions']])) for doc in r]
        else:
            results = [doc[self.sourcepage_field] + ": " + nonewlines(doc[self.content_field]) for doc in r]
        content = "\n".join(results)

        prompt = (overrides.get("prompt_template") or self.template).format(q=q, retrieved=content)
        completion = openai.Completion.create(
            engine=self.openai_deployment, 
            prompt=prompt, 
            temperature=overrides.get("temperature") or 0.3, 
            max_tokens=1024, 
            n=1, 
            stop=["\n"])

        return {"data_points": results, "answer": completion.choices[0].text, "thoughts": f"Question:<br>{q}<br><br>Prompt:<br>" + prompt.replace('\n', '<br>')}
