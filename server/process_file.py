# -*- coding: utf-8 -*-

from collections import OrderedDict
import argparse
import json
import os
import re

from llama_index.core import get_response_synthesizer
from llama_index.core import QueryBundle
from llama_index.core import VectorStoreIndex
from llama_index.core.node_parser import (
    SemanticSplitterNodeParser
)

from llama_index.core.postprocessor.types import BaseNodePostprocessor
from llama_index.core.postprocessor import KeywordNodePostprocessor
from llama_index.core.postprocessor import LLMRerank

# Current github issue here (rerank is still useful) :
# https://github.com/run-llama/llama_index/issues/11093
class SafeLLMRerank:
    def __init__(self, choice_batch_size=5, top_n=2):
        self.choice_batch_size = choice_batch_size
        self.top_n = top_n
        self.reranker = LLMRerank(
            choice_batch_size=choice_batch_size,
            top_n=top_n,
        )

    def postprocess_nodes(self, nodes, query_bundle):
        try:
            return self.reranker.postprocess_nodes(nodes, query_bundle)
        except Exception as e:
            print(f"Rerank issue: {e}")
            return nodes

from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.query_engine import MultiStepQueryEngine
from llama_index.core.retrievers import RecursiveRetriever
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.embeddings.together import TogetherEmbedding
from llama_index.llms.openai import OpenAI

import nest_asyncio
import requests

nest_asyncio.apply()

from llama_index.core.schema import IndexNode, TextNode, NodeRelationship, RelatedNodeInfo

# Current github issue here (rerank is still useful) :
# https://github.com/run-llama/llama_index/issues/11093
class SafeLLMRerank:
    def __init__(self, choice_batch_size=5, top_n=2):
        self.choice_batch_size = choice_batch_size
        self.top_n = top_n
        self.reranker = LLMRerank(
            choice_batch_size=choice_batch_size,
            top_n=top_n,
        )

    def postprocess_nodes(self, nodes, query_bundle):
        try:
            return self.reranker.postprocess_nodes(nodes, query_bundle)
        except Exception as e:
            print(f"Rerank issue: {e}")
            return nodes

from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.query_engine import MultiStepQueryEngine
from llama_index.core.retrievers import RecursiveRetriever
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI

import nest_asyncio
import requests

nest_asyncio.apply()

from llama_index.core.schema import IndexNode, TextNode, NodeRelationship, RelatedNodeInfo

def send_update(message):
    """
    Sending updates to the frontend about progress through the backend.
    """
    update_url = 'http://localhost:8080/api/upload/status/update'
    if update_url:
        try:
            requests.post(update_url, json={'status': message})
        except Exception as e:
            print(f"Failed to send update: {e}")

def process_file(filename):

    ## Get Environmental Variables

    togetherai_api_key = os.getenv('TOGETHERAI_API_KEY')
    openai_api_key = os.getenv('OPENAI_API_KEY')

    """## Load Data and Setup"""

    class SectionNumberer:
        """
        When converting tex files to pdfs in overleaf, sections become numbered before appendix.
        In the appendix, they are num
        and during appendix they are lettered.
        This function mimic that behavior by converting the sections
        """
        def __init__(self):
            self.section_count = 0
            self.subsection_count = 0
            self.alpha_section_count = 0
            self.bibliography_found = False  # Flag to track if bibliography has been found

        def replace_heading(self, match):
            command = match.group(1)  # 'section', 'subsection', or 'bibliography'
            content = match.group(2)  # Title inside the braces

            # If bibliography command is encountered, switch to alphabetic numbering
            if command == 'bibliography':
                self.bibliography_found = True
                return match.group(0)  # Optionally return the bibliography line unchanged

            # Process sections and subsections based on the numbering mode
            if self.bibliography_found:
                if command == 'section':
                    self.alpha_section_count += 1
                    section_label = chr(64 + self.alpha_section_count)  # Convert to letters A, B, C, etc.
                    self.subsection_count = 0  # Reset subsection count for new section
                    return f"\\section{{{section_label} {content}}}"
                elif command == 'subsection':
                    self.subsection_count += 1
                    subsection_label = f"{chr(64 + self.alpha_section_count)}.{self.subsection_count}"
                    return f"\\subsection{{{subsection_label} {content}}}"
            else:
                if command == 'section':
                    self.section_count += 1
                    self.subsection_count = 0  # Reset subsection count
                    return f"\\section{{{self.section_count} {content}}}"
                elif command == 'subsection':
                    self.subsection_count += 1
                    return f"\\subsection{{{self.section_count}.{self.subsection_count} {content}}}"

        def number_sections(self, tex_content):
            # Regex to find all section, subsection, or bibliography commands
            pattern = re.compile(r"\\(section|subsection|bibliography)\{([^}]*)\}")
            processed_content = pattern.sub(self.replace_heading, tex_content)
            return processed_content

    def extract_text_and_captions_table(latex_string):
        """
        Remove tables, but keep the table captions (they are numbered).
        """

        # Regex to find all table environments (both \begin{table*} and \begin{table})
        table_pattern = re.compile(r'(\\begin\{table\*?\}.*?\\end\{table\*?\})', re.DOTALL)

        # Split the text at each table environment
        parts = table_pattern.split(latex_string)

        result_parts = []
        caption_counter = 1

        for part in parts:
            if table_pattern.match(part):
                # Find the caption within this table
                caption_match = re.search(r'\\caption\{([^}]*)\}', part)
                if caption_match:
                    caption_text = caption_match.group(1)
                    result_parts.append(f'Table {caption_counter} Description: {caption_text}. End Table {caption_counter} Description.')
                    caption_counter += 1
            else:
                result_parts.append(part)

        # Combine the extracted text parts and captions
        combined_text = ' '.join(result_parts)

        # Clean up any extra spaces introduced
        clean_text = re.sub(r'\s+', ' ', combined_text).strip()

        return clean_text

    def extract_text_and_captions_figure(latex_string):
        """
        Remove figures, but keep the figure captions (they are numbered).
        """

        # Regex to find all figure environments (both \begin{figure*} and \begin{figure})
        table_pattern = re.compile(r'(\\begin\{figure\*?\}.*?\\end\{figure\*?\})', re.DOTALL)

        # Split the text at each figure environment
        parts = table_pattern.split(latex_string)

        result_parts = []
        caption_counter = 1

        for part in parts:
            if table_pattern.match(part):
                # Find the caption within this figure
                caption_match = re.search(r'\\caption\{([^}]*)\}', part)
                if caption_match:
                    caption_text = caption_match.group(1)
                    result_parts.append(f'Figure {caption_counter} Description: {caption_text}. End Figure {caption_counter} Description.')
                    caption_counter += 1
            else:
                result_parts.append(part)

        # Combine the extracted text parts and captions
        combined_text = ' '.join(result_parts)

        # Clean up any extra spaces introduced
        clean_text = re.sub(r'\s+', ' ', combined_text).strip()

        return clean_text

    def read_latex_doc(filename):

        send_update("Parsing Latex Information")

        with open(filename, 'r') as file:
            tex_content = file.read()

        def extract_title(tex_content):
            """
            This is meant to go to the source in all nodes
            """

            # Regex pattern to match text within \title{...}
            pattern = re.compile(r'\\title\{([^}]*)\}')
            result = pattern.search(tex_content)
            return result.group(1) if result else ''

        def remove_document_tags(tex_content):
            """
            Remove \begin{document} and \end{document} from LaTeX content.
            """
            tex_content = re.sub(r'\\begin{document}', '', tex_content)
            tex_content = re.sub(r'\\end{document}', '', tex_content)
            return tex_content

        def start_with_abstract(tex_content):
            """
            Keep only the content starting from \begin{abstract}.
            """
            match = re.search(r'\\begin{abstract}', tex_content)
            if match:
                tex_content = tex_content[match.start():]
            return tex_content

        def remove_comments(tex_content):
            """
            Remove commented lines from LaTeX content while preserving original line endings.
            """
            lines = re.split('(\r\n|\r|\n)', tex_content)  # Capture the line endings
            uncommented_lines = [line for line in lines if not line.strip().startswith('%') and not re.match(r'(\r\n|\r|\n)', line)]
            line_endings = [line for line in lines if re.match(r'(\r\n|\r|\n)', line)]

            # Reconstruct the text preserving line endings
            uncommented_text = ''.join(uncommented_lines + line_endings)
            return uncommented_text

        def add_spaces_around_commands(text, commands):
            for command in commands:
                # Create a regular expression pattern for each command, including optional *
                pattern = rf'(\\{command}\*?\{{.*?\}})'

                # Add spaces around each matched command pattern
                text = re.sub(pattern, r' \1 ', text)

            # Remove any duplicate spaces that may have been introduced
            text = re.sub(r'\s+', ' ', text).strip()

            return text

        def remove_consecutive_occurrences(line):
            # Use a regular expression to replace consecutive occurrences of %%
            # Some people use multiple line strings
            return re.sub(r'(%%)+', r'\1', line)

        def number_sections(tex_content):
            section_count = 0
            appendix_mode = False
            alpha_section_count = 0
            subsection_count = 0  # Initialize subsection count

            def replace_heading(match):
                nonlocal section_count, alpha_section_count, appendix_mode, subsection_count
                heading_type = match.group(1)  # Determine whether it's 'section' or 'subsection'
                heading_content = match.group(2)  # Capture the title inside the braces

                if "\\appendix" in heading_content:
                    appendix_mode = True
                    return match.group(0)  # Return the original line

                if heading_type == 'section':
                    if appendix_mode:
                        alpha_section_count += 1
                        section_label = chr(64 + alpha_section_count)
                        subsection_count = 0  # Reset subsection count
                        return f"\\section{{{section_label}. {heading_content}}}"
                    else:
                        section_count += 1
                        subsection_count = 0  # Reset subsection count
                        return f"\\section{{{section_count}. {heading_content}}}"
                elif heading_type == 'subsection':
                    if appendix_mode:
                        subsection_count += 1
                        subsection_label = f"{chr(64 + alpha_section_count)}.{subsection_count}"
                        return f"\\subsection{{{subsection_label}. {heading_content}}}"
                    else:
                        subsection_count += 1
                        return f"\\subsection{{{section_count}.{subsection_count}. {heading_content}}}"

            # Regex to find all section and subsection commands
            pattern = re.compile(r"\\(section|subsection)\{([^}]*)\}")
            processed_content = pattern.sub(replace_heading, tex_content)
            return processed_content

        def split_sections(tex_content):
            send_update("Performing semantic chunking")
            # Split using lookahead to ensure \section starts a new chunk
            # This splits before each \section{...}
            chunks = re.split(r'(?=\\section\*?{[^}]*})', tex_content)

            # Initialize list to store properly combined chunks
            combined_chunks = []

            # Append the first chunk directly as it includes content before any \section
            if chunks and not chunks[0].startswith('\\section'):
                combined_chunks.append(chunks.pop(0))

            # Remaining chunks should already start with \section
            combined_chunks.extend(chunks)

            return combined_chunks

        # Remove \begin{document} and \end{document}
        tex_content = remove_document_tags(tex_content)

        # List of LaTeX commands to handle that can add spaces where non exist. This is extremely important for LLMs to chunk.
        commands = ['footnote', 'href', 'textbf', 'section', 'section*', 'subsection', 'subsection*']

        tex_content = add_spaces_around_commands(tex_content, commands)

        # Remove most of table content except caption.
        tex_content = extract_text_and_captions_table(tex_content)

        # Remove most of table content except caption.
        tex_content = extract_text_and_captions_figure(tex_content)

        # Start with \begin{abstract}
        tex_content = start_with_abstract(tex_content)

        # Remove commented lines
        tex_content = remove_comments(tex_content)

        # Remove multiple line comments.
        tex_content = remove_consecutive_occurrences(tex_content)

        # Create an instance of SectionNumberer and process the LaTeX content
        numberer = SectionNumberer()
        tex_content = numberer.number_sections(tex_content)

        list_chunks = split_sections(tex_content)

        # Regex pattern to match strings starting with \section*{Acknowledgements} or \section{Acknowledgements} (case-insensitive)
        pattern = re.compile(r'\\section\*?\{acknowledgements\}', re.IGNORECASE)

        # Filter out items that match the pattern
        list_chunks = [chunk for chunk in list_chunks if not pattern.match(chunk)]

        # Replace \begin{abstract} with \section*{abstract}
        list_chunks[0] = list_chunks[0].replace('\\begin{abstract}', '\\section*{abstract}')

        # Replace \end{abstract} with an empty string
        list_chunks[0] = list_chunks[0].replace('\\end{abstract}', '')

        # Extract the title content
        title = extract_title(tex_content)

        return(list_chunks, title)

    list_chunks, title = read_latex_doc(filename)


    """## Parsing Documents into Text Chunks (Nodes)"""

    def extract_text(text):
        # Regex pattern to match text within curly braces for all specified cases
        pattern = re.compile(r'\\(?:begin|section\*?)\{([^}]*)\}')
        result = pattern.search(text)
        return result.group(1) if result else ''

    def check_license(node1):
        """
        This is just an experiment with metadata for licenses. Future work.
        """
        normalized_node = node1.lower().replace('-', ' ')
        if 'cc by nc 4.0' in normalized_node:
            return 'CC BY-NC 4.0'
        else:
            return ''

    # concatenate the names of node 0 and 1 (abstract and introduction) for A3
    node_ids = []

    base_nodes = []
    for chunk in list_chunks:
        node_id = extract_text(chunk)
        node_ids.append(node_id)
        base_nodes.append(TextNode(text=chunk, id_=node_id))
        #base_nodes.append(TextNode(text=chunk, id_=node_id, metadata = {'license': check_license(chunk)}))

    # Check if there are at least two node_ids to concatenate (for question A3)
    if len(node_ids) >= 2:
        combined_node_id = '/'.join(node_ids[:2])  # Concatenate the first two node_ids
    else:
        combined_node_id = None  # Handle cases where there are less than two node_ids

    # Add relationships between nodes

    for i, node in enumerate(base_nodes):
        if i < len(base_nodes) - 1:
            next_node = base_nodes[i + 1]
            node.relationships[NodeRelationship.NEXT] = RelatedNodeInfo(
                node_id=next_node.id_
            )
        if i > 0:
            previous_node = base_nodes[i - 1]
            node.relationships[NodeRelationship.PREVIOUS] = RelatedNodeInfo(
                node_id=previous_node.id_
            )

    # Adding section names and basic prompt instructions to each prompt
    section_names = []
    for node in base_nodes:
        section_names.append(node.id_)

    # Papers missing a limitations section are desk rejected
    # https://aclrollingreview.org/cfp
    if not any('Limitation' in section for section in section_names):
        A1_issue = 1
    else:
        A1_issue = 0

    # Join the node names with commas and the last one with 'and', all enclosed in single quotes
    quoted_names = [f"'{name}'" for name in section_names]
    section_names_text = ', '.join(quoted_names[:-1]) + ', and ' + quoted_names[-1]

    prompt_instruction = f"""If the the answer is 'YES', provide the section name.
    Only return valid section names which are {section_names_text}.
    If the answer is 'NO' or 'NOT APPLICABLE', the section name is 'None'.
    Provide a step by step justification for the answer.
    Format your response as a JSON object with 'answer', 'section name', and 'justification' as the keys.
    If the information isn't present, use 'unknown' as the value."""

    prompt_instruction_A3 = f"""If the the answer is 'YES', provide the section name.
    Only return valid section names which are '{combined_node_id}'.
    If the answer is 'NO' or 'NOT APPLICABLE', the section name is 'None'.
    Provide a step by step justification for the answer.
    Format your response as a JSON object with 'answer', 'section name', and 'justification' as the keys.
    If the information isn't present, use 'unknown' as the value."""

    # Supporting information is taken from https://aclrollingreview.org/responsibleNLPresearch/
    supporting_prompt_dict = OrderedDict()
    supporting_prompt_dict["A1"] = """Point out any strong assumptions and how robust your results are to violations of these assumptions (e.g., independence assumptions, noiseless settings, model well-specification, asymptotic approximations only held locally). Reflect on how these assumptions might be violated in practice and what the implications would be.
    Reflect on the scope of your claims, e.g., if you only tested your approach on a few datasets, languages, or did a few runs. In general, empirical results often depend on implicit assumptions, which should be articulated. Reflect on the factors that influence the performance of your approach. For example, a speech-to-text system might not be able to be reliably used to provide closed captions for online lectures because it fails to handle technical jargon.
    If you analyze model biases: state the definition of bias you are using. State the motivation and definition explicitly."""

    supporting_prompt_dict["A2"] = """Examples of risks include potential malicious or unintended harmful effects and uses (e.g., disinformation, generating fake profiles, surveillance), environmental impact (e.g., training huge models), fairness considerations (e.g., deployment of technologies that could further disadvantage or exclude historically disadvantaged groups), privacy considerations (e.g., a paper on model/data stealing), and security considerations (e.g., adversarial attacks).
    Consider if the research contributes to overgeneralization, bias confirmation, under or overexposure of specific languages, topics, or applications at the expense of others.
    We expect many papers to be foundational research and not tied to particular applications, let alone deployments. However, we encourage authors to discuss potential risks if they see a path to any positive or negative applications. For example, the authors can emphasize how their systems are intended to be used, how they can safeguard their systems against misuse, or propose future research directions.
    Consider different stakeholders that could be impacted by your work. Consider if it possible that research benefits some stakeholders while harming others. Consider if it pays special attention to vulnerable or marginalized communities. Consider if the research leads to exclusion of certain groups.
    Consider dual use, i.e, possible benefits or harms that could arise when the technology is being used as intended and functioning correctly, benefits or harms that could arise when the technology is being used as intended but gives incorrect results, and benefits or harms following from (intentional or unintentional) misuse of the technology.
    Consider citing previous work on relevant mitigation strategies for the potential risks of the work (e.g., gated release of models, providing defenses in addition to attacks, mechanisms for monitoring misuse, mechanisms to monitor how a system learns from feedback over time, improving the efficiency and accessibility of NLP)."""

    supporting_prompt_dict["A3"] = """The main claims in the paper should be clearly stated in the abstract and in the introduction.
    These claims should be supported by evidence presented in the paper, potentially in the form of experimental results, reasoning, or theory. The connection between which evidence supports which claims should be clear.
    The context of the contributions of the paper should be clearly described, and it should be stated how much the results would be expected to generalize to other contexts.
    It should be easy for a casual reader to distinguish between the contributions of the paper and open questions, future work, aspirational goals, motivations, etc."""

    supporting_prompt_dict["B1"] = """For composite artifacts like the GLUE benchmark, this means all creators. Cite the original paper that produced the code package or dataset. Remember to state which version of the asset you’re using."""

    supporting_prompt_dict["B2"] = """State the name of the license (e.g., CC-BY 4.0) for each asset.
    If you scraped or collected data from a particular source (e.g., website or social media API), you should state the copyright and terms of service of that source.
    Please note that some sources do not allow inference of protected categories like gender, sexual orientation, health status, etc. The data might be in public domain and licensed for research purposes. The data might be used with consent of its creators or copyright holders.
    If the data is used without consent, the paper makes the case to justify its legal basis (e.g., research performed in the public interest under GDPR).
    If you are releasing assets, you should include a license, copyright information, and terms of use in the package.
    If you are repackaging an existing dataset, you should state the original license as well as the one for the derived asset (if it has changed).
    If you cannot find this information online, you are encouraged to reach out to the asset’s creators."""

    supporting_prompt_dict["B3"] = """For the artifacts you create, specify the intended use and whether that is compatible with the original access conditions (in particular, derivatives of data accessed for research purposes should not be used outside of research contexts).
    Data and/or pretrained models are released under a specified license that is compatible with the conditions under which access to data was granted (in particular, derivatives of data accessed for research purposes should not be deployed in the real world as anything other than a research prototype, especially commercially).
    The paper specifies the efforts to limit the potential use to circumstances in which the data/models could be used safely (such as an accompanying data/model statement).
    The data is sufficiently anonymized to make identification of individuals impossible without significant effort. If this is not possible due to the research type, please state so explicitly and explain why.
    The paper discusses the harms that may ensue from the limitations of the data collection methodology, especially concerning marginalized/vulnerable populations, and specifies the scope within which the data can be used safely."""

    supporting_prompt_dict["B4"] = """There are some settings where the existence of offensive content is not necessarily bad (e.g., swear words occur naturally in text), or part of the research question (i.e., hate speech). This question is just to encourage discussion of potentially undesirable properties.
    Explain how you checked for offensive content and identifiers (e.g., with a script, manually on a sample, etc.).
    Explain how you anonymized the data, i.e., removed identifying information like names, phone and credit card numbers, addresses, user names, etc. Examples are monodirectional hashes, replacement, or removal of data points. If anonymization is not possible due to the nature of the research (e.g., author identification), explain why.
    List any further privacy protection measures you are using: separation of author metadata from text, licensing, etc.
    If any personal data is used: the paper specifies the standards applied for its storage and processing, and any anonymization efforts.
    If the individual speakers remain identifiable via search: the paper discusses possible harms from misuse of this data, and their mitigation."""

    supporting_prompt_dict["B5"] = """Scientific artifacts may include code, data, models or other artifacts. Be sure to report the language of any language data, even if it is commonly-used benchmarks.
    Describe basic information about the data that was used, such as the domain of the text, any information about the demographics of the authors, etc."""

    supporting_prompt_dict["B6"] = """Even for commonly-used benchmark datasets, include the number of examples in train / validation / test splits, as these provide necessary context for a reader to understand experimental results. For example, small differences in accuracy on large test sets may be significant, while on small test sets they may not be."""

    supporting_prompt_dict["C1"] = """Even for commonly-used models like BERT, reporting the number of parameters is important because it provides context necessary for readers to understand experimental results. The size of a model has an impact on performance, and it shouldn’t be up to a reader to have to go look up the number of parameters in models to remind themselves of this information."""

    supporting_prompt_dict["C2"] = """The experimental setup should include information about exactly how experiments were set up, like how model selection was done (e.g., early stopping on validation data, the single model with the lowest loss, etc.), how data was preprocessed, etc.
    Many research projects involve manually tuning hyperparameters until some “good” values are found, and then running a final experiment which is reported in the paper. Other projects involve using random search or grid search to find hyperparameters. In all cases, report the results of such experiments, even if they were stopped early or didn’t lead to your best results, as it allows a reader to know the process necessary to get to the final result and to estimate which hyperparameters were important to tune.
    Be sure to include the best-found hyperparameter values (e.g., learning rate, regularization, etc.) as these are critically important for others to build on your work.
    The experimental setup should likely be described in the main body of the paper, as that is important for reviewers to understand the results, but large tables of hyperparameters or the results of hyperparameter searches could be presented in the main paper or appendix."""

    supporting_prompt_dict["C3"] = """Error bars can be computed by running experiments with different random seeds, Clopper–Pearson confidence intervals can be placed around the results (e.g., accuracy), or expected validation performance can be useful tools here.
    In all cases, when a result is reported, it should be clear if it is from a single run, the max across N random seeds, the average, etc.
    When reporting a result on a test set, be sure to report a result of the same model on the validation set (if available) so others reproducing your work don’t need to evaluate on the test set to confirm a reproduction."""

    supporting_prompt_dict["C4"] = """The version number or reference to specific implementation is important because different implementations of the same metric can lead to slightly different results (e.g., ROUGE).
    The paper cites the original work for the model or software package. If no paper exists, a URL to the website or repository is included.
    If you modified an existing library, explain what changes you made."""

    supporting_prompt_dict["D1"] = """Examples of risks include a crowdsourcing experiment which might show offensive content or collect personal identifying information (PII). Ideally, the participants should be warned.
    Including this information in the supplemental material is fine, but if the main contribution of your paper involves human subjects, then we strongly encourage you to include as much detail as possible in the main paper."""

    supporting_prompt_dict["D2"] = """Be explicit about how you recruited your participants. For instance, mention the specific crowdsourcing platform used. If participants are students, give information about the population (e.g., graduate/undergraduate, from a specific field), and how they were compensated (e.g., for course credit or through payment).
    In case of payment, provide the amount paid for each task (including any bonuses), and discuss how you determined the amount of time a task would take. Include discussion on how the wage was determined and how you determined that this was a fair wage."""

    supporting_prompt_dict["D3"] = """For example, if the was collect via crowdsourcing, the instructions should explain to crowdworkers how the data would be used."""

    supporting_prompt_dict["D4"] = """Depending on the country in which research is conducted, ethics review (e.g., from an IRB board in the US context) may be required for any human subjects research. If an ethics review board was involved, you should clearly state it in the paper. However, stating that you obtained approval from an ethics review board does not imply that the societal impact of the work does not need to be discussed.
    For initial submissions, do not include any information that would break anonymity, such as the institution conducting the review."""

    supporting_prompt_dict["D5"] = """State if your data include any protected information (e.g., sexual orientation or political views under GDPR).
    The paper is accompanied by a data statement describing the basic demographic and geographic characteristics of the author population that is the source of the data, and the population that it is intended to represent.
    If applicable: the paper describes whether any characteristics of the human subjects were self-reported (preferably) or inferred (in what way), justifying the methodology and choice of description categories."""

    prompt_dict = OrderedDict()

    ## A for Every Submission
    ###
    prompt_dict["A1"] = f"""Introduction: Behave like you are the author of a paper you are going to submit to a conference.
    Question: Did you describe the limitations of your work?
    Additional Context: {supporting_prompt_dict["A1"]}
    Output Structure: """ + prompt_instruction

    prompt_dict["A2"] = f"""Introduction: Behave like you are the author of a paper you are going to submit to a conference.
    Question: Did you discuss any potential risks of your work?
    Additional Context: {supporting_prompt_dict["A2"]}
    Output Structure: """ + prompt_instruction

    prompt_dict["A3"] = f"""Introduction: Behave like you are the author of a paper you are going to submit to a conference.
    Question: Does the {combined_node_id} summarize the paper’s main claims?
    Additional Context: {supporting_prompt_dict["A3"]}
    Output Structure: """ + prompt_instruction_A3

    ## B Did you use or create scientific artifacts?
    ###
    prompt_dict["B1"] = f"""Introduction: Behave like you are the author of a paper you are going to submit to a conference. Scientific artifacts may include code, data, models or other artifacts.
    Question: Did you cite the creators of artifacts you used?
    #Additional Context: {supporting_prompt_dict["B1"]}
    Output Structure: """ + prompt_instruction

    prompt_dict["B2"] = f"""Introduction: Behave like you are the author of a paper you are going to submit to a conference. Scientific artifacts may include code, data, models or other artifacts.
    Question: Did you discuss the license or terms for use and/or distribution of any scientific artifacts?
    Additional Context: {supporting_prompt_dict["B2"]}
    Output Structure: """ + prompt_instruction

    prompt_dict["B3"] = f"""Introduction: Behave like you are the author of a paper you are going to submit to a conference. Scientific artifacts may include code, data, models or other artifacts.
    Question: Did you discuss if your use of existing artifact(s) was consistent with their intended use, provided that it was specified?
    Additional Context: {supporting_prompt_dict["B3"]}
    Output Structure: """ + prompt_instruction

    prompt_dict["B4"] = f"""Introduction: Behave like you are the author of a paper you are going to submit to a conference.
    Question: Did you discuss the steps taken to check whether the data that was collected / used contains any information that names or uniquely identifies individual people or offensive content, and the steps taken to protect / anonymize it?
    Additional Context: {supporting_prompt_dict["B4"]}
    Output Structure: """ + prompt_instruction

    prompt_dict["B5"] = f"""Introduction: Behave like you are the author of a paper you are going to submit to a conference.
    Scientific artifacts may include code, data, models or other artifacts. Question: Did you provide documentation of the artifacts, e.g., coverage of domains, languages, and linguistic phenomena, demographic groups represented, etc.?
    Additional Context: {supporting_prompt_dict["B5"]}
    Output Structure: """ + prompt_instruction

    prompt_dict["B6"] = f"""Introduction: Behave like you are the author of a paper you are going to submit to a conference.
    Did you report relevant statistics like the number of examples, details of train / test / dev splits, etc. for the data that you used / created?
    Additional Context: {supporting_prompt_dict["B6"]}
    Output Structure: """ + prompt_instruction

    ## C Did you run computational experiments
    ###
    prompt_dict["C1"] = f"""Introduction: Behave like you are the author of a paper you are going to submit to a conference.
    Question: Did you report the number of parameters in the models used, the total computational budget (e.g., GPU hours), or computing infrastructure used?
    Additional Context: {supporting_prompt_dict["C1"]}
    Output Structure: """ + prompt_instruction

    prompt_dict["C2"] = f"""Introduction: Behave like you are the author of a paper you are going to submit to a conference.
    Question: Did you discuss the experimental setup, including hyperparameter search and best-found hyperparameter values?
    Additional Context: {supporting_prompt_dict["C2"]}
    Output Structure: """ + prompt_instruction

    prompt_dict["C3"] = f"""Introduction: Behave like you are the author of a paper you are going to submit to a conference.
    Question: Did you report descriptive statistics about your results (e.g., error bars around results, summary statistics from sets of experiments), and is it transparent whether you are reporting the max, mean, etc. or just a single run?
    Additional Context: {supporting_prompt_dict["C3"]}
    Output Structure: """ + prompt_instruction

    prompt_dict["C4"] = f"""Introduction: Behave like you are the author of a paper you are going to submit to a conference.
    Question: If you used existing packages (e.g., for preprocessing, for normalization, or for evaluation), did you report the implementation, model, and parameter settings used (e.g., NLTK, Spacy, ROUGE, etc.)?
    Additional Context: {supporting_prompt_dict["C4"]}
    Output Structure: """ + prompt_instruction

    ## D Did you use human annotators (e.g., crowdworkers) or research with human participants?
    ###
    prompt_dict["D1"] = f"""Introduction: Behave like you are the author of a paper you are going to submit to a conference.
    Question: Did you report the full text of instructions given to participants, including e.g., screenshots, disclaimers of any risks to participants or annotators, etc.?
    Additional Context: {supporting_prompt_dict["D1"]}
    Output Structure: """ + prompt_instruction

    prompt_dict["D2"] = f"""Introduction: Behave like you are the author of a paper you are going to submit to a conference.
    Question: Did you report information about how you recruited (e.g., crowdsourcing platform, students) and paid participants, and discuss if such payment is adequate given the participants’ demographic (e.g., country of residence)?
    Additional Context: {supporting_prompt_dict["D2"]}
    Output Structure: """ + prompt_instruction

    prompt_dict["D3"] = f"""Introduction: Behave like you are the author of a paper you are going to submit to a conference.
    Question: Did you discuss whether and how consent was obtained from people whose data you’re using/curating?
    Additional Context: {supporting_prompt_dict["D3"]}
    Output Structure: """ + prompt_instruction

    prompt_dict["D4"] = f"""Introduction: Behave like you are the author of a paper you are going to submit to a conference.
    Question: Was the data collection protocol approved (or determined exempt) by an ethics review board?
    Additional Context: {supporting_prompt_dict["D4"]}
    Output Structure: """ + prompt_instruction

    prompt_dict["D5"] = f"""Introduction: Behave like you are the author of a paper you are going to submit to a conference.
    Question: Did you report the basic demographic and geographic characteristics of the annotator population that is the source of the data?
    Additional Context: {supporting_prompt_dict["D5"]}
    Output Structure: """ + prompt_instruction

    ## E Did you use AI assistants (e.g., ChatGPT, Copilot) in your research, coding, or writing?
    ###

    # E1. Did you include information about your use of AI assistants?

    # E1. Elaboration For Yes Or No. For yes, provide a section number. For no, justify why not.

    # E1. Section Or Justification

    # https://platform.openai.com/docs/guides/embeddings/what-are-embeddings
    embed_model = OpenAIEmbedding(model = 'text-embedding-ada-002')
    #embed_model = TogetherEmbedding(model_name="togethercomputer/m2-bert-80M-8k-retrieval", api_key = togetherai_api_key)

    model_name = "gpt-3.5-turbo"
    #model_name = "gpt-4o-2024-05-13"
    llm = OpenAI(api_key=openai_api_key, temperature=0, model=model_name, chunk_size_limit=2048, )

    #model_name = 'Llama-3-70b-chat-hf'

    #model_source = 'meta-llama'
    #model_name = f'{model_source}/Meta-Llama-3.1-70B-Instruct-Turbo'
    #llm = OpenAI(api_key=togetherai_api_key, temperature=0, model = model_name,base_url='https://api.together.xyz')

    """# Chunk References: Smaller Child Chunks Referring to Bigger Parent Chunk

    In this usage example, we show how to build a graph of smaller chunks pointing to bigger parent chunks.

    During query-time, we retrieve smaller chunks, but we follow references to bigger chunks. This allows us to have more context for synthesis.
    """

    # If the backend comes across issues that the author might like to know about
    # these issues will be provided to the author (e.g., papers missing limitations section get desk rejected)
    issue_dict = {'A1': (A1_issue, 'Paper does not have a limitations section which according to https://aclrollingreview.org/cfp means the paper will get desk rejected.'),
                        'A2': (0, ''),
                        'A3': (0, ''),
                        'B1': (0, ''),
                        'B2': (0, ''),
                        'B3': (0, ''),
                        'B4': (0, ''),
                        'B5': (0, ''),
                        'B6': (0, ''),
                        'C1': (0, ''),
                        'C2': (0, ''),
                        'C3': (0, ''),
                        'C4': (0, ''),
                        'D1': (0, ''),
                        'D2': (0, ''),
                        'D3': (0, ''),
                        'D4': (0, ''),
                        'D5': (0, ''),
                        'E1': (0, '')
                        }

    sub_node_parsers = [SemanticSplitterNodeParser(buffer_size=1,
                                                breakpoint_percentile_threshold=95,
                                                embed_model=embed_model,
                                                include_metadata = True,
                                                include_prev_next_rel = True),]
    all_nodes = []
    send_update("Performing Embeddings")

    for base_node in base_nodes:
        for n in sub_node_parsers:
            sub_nodes = n.get_nodes_from_documents([base_node])
            sub_inodes = [
                IndexNode.from_text_node(sn, base_node.node_id) for sn in sub_nodes
            ]
            all_nodes.extend(sub_inodes)

        # also add original node to node
        original_node = IndexNode.from_text_node(base_node, base_node.node_id)
        all_nodes.append(original_node)

    all_nodes_dict = {n.node_id: n for n in all_nodes}

    index = VectorStoreIndex(all_nodes, embed_model=embed_model)


    # A1: Criterion for filtering nodes
    def is_limitation_node(node):
        return 'Limitation' in node.node_id

    # Filter the nodes based on the criterion
    A1_filtered_nodes = {node_id: node for node_id, node in all_nodes_dict.items() if is_limitation_node(node)}



    vector_retriever_chunk = index.as_retriever(similarity_top_k=40)

    recursive_retriever = RecursiveRetriever(
        "vector",
        retriever_dict={"vector": vector_retriever_chunk},
        node_dict=all_nodes_dict,
        verbose=False,
    )

    # https://docs.llamaindex.ai/en/v0.10.17/module_guides/deploying/query_engine/response_modes.html
    response_synthesizer = get_response_synthesizer(response_mode="tree_summarize")

    query_engine = RetrieverQueryEngine.from_args(
        recursive_retriever,
        response_synthesizer=response_synthesizer,
        llm=llm,
    )

    """## Outputting JSON Response."""

    results = {}

    send_update("Running inference")
    for index ,key in enumerate(prompt_dict.keys()):
        send_update(f"Running Inference for Section {key[0]}")
        response = query_engine.query(prompt_dict[key])
        temp_dict = json.loads(response.response.replace('\\', '\\\\'))
        temp_dict['prompt'] = prompt_dict[key]
        temp_dict['llm'] = model_name
        results[key] = temp_dict

    results['issues'] = issue_dict

    send_update("Inferencing Complete")

    return results
