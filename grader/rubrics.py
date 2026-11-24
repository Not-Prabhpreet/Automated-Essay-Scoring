"""Kev rubric questions, worded from the ASAP essay set descriptions
(data/Essay_Set_Descriptions/*.docx).

Each question is a Kev `score` question (README "API": criteria are "descriptions,
ordered from lowest to highest"; the answer's `score` is the mean level index starting
at 0). Level descriptions are the rubric's own sentences; for set 8 we keep each level's
lead sentences and drop the long "The writing is characterized by ..." bullet lists.

`holistic` asks for one rater's rubric score; `to_domain1` converts Kev's answers to
the set's resolved (domain1) scale with the adjudication rule from the set description,
so Kev can be compared with the main model on the same scale.
"""
from __future__ import annotations

from typing import Dict, List

PROMPTS: Dict[int, str] = {
    1: "Write a letter to your local newspaper in which you state your opinion on the effects computers have on people. Persuade the readers to agree with you.",
    2: "Write a persuasive essay to a newspaper reflecting your views on censorship in libraries. Do you believe that certain materials, such as books, music, movies, magazines, etc., should be removed from the shelves if they are found offensive? Support your position with convincing arguments from your own experience, observations, and/or reading.",
    3: "Write a response that explains how the features of the setting affect the cyclist. In your response, include examples from the essay that support your conclusion.",
    4: "Write a response that explains why the author concludes the story with this paragraph: \"When they come back, Saeng vowed silently to herself, in the spring, when the snows melt and the geese return and this hibiscus is budding, then I will take that test again.\" Include details and examples from the story that support your ideas.",
    5: "Describe the mood created by the author in the memoir. Support your answer with relevant and specific information from the memoir.",
    6: "Based on the excerpt, describe the obstacles the builders of the Empire State Building faced in attempting to allow dirigibles to dock there. Support your answer with relevant and specific information from the excerpt.",
    7: "Write about patience. Do only one of the following: write a story about a time when you were patient OR write a story about a time when someone you know was patient OR write a story in your own way about patience.",
    8: "Tell a true story in which laughter was one element or part.",
}

# Holistic rubric levels, lowest first (one rater's scale).
_HOLISTIC: Dict[int, List[str]] = {
    1: [
        "An undeveloped response that may take a position but offers no more than very minimal support.",
        "An under-developed response that may or may not take a position.",
        "A minimally-developed response that may take a position, but with inadequate support and details.",
        "A somewhat-developed response that takes a position and provides adequate support.",
        "A developed response that takes a clear position and provides reasonably persuasive support.",
        "A well-developed response that takes a clear and thoughtful position and provides persuasive support.",
    ],
    2: [
        "Fails to accomplish the task. It exhibits considerable difficulty in areas of development, organization, and writing style; generally either very brief or rambling and repetitive.",
        "Only partially accomplishes the task. It may have difficulty maintaining a focus, or be too brief to provide sufficient development, organization or writing style.",
        "Minimally accomplishes the task. Some elements of development, organization, and writing style are weak.",
        "A good performance. It accomplishes the task, but generally needs more development, better organization, or a more sophisticated writing style.",
        "A solid performance. It fully accomplishes the task, but lacks the overall level of sophistication and consistency of a top paper.",
        "Rare. It fully accomplishes the task in a thorough and insightful manner and has a distinctive quality that sets it apart as an outstanding performance.",
    ],
    3: [
        "The response is completely irrelevant or incorrect, or there is no response.",
        "The response shows evidence of a minimal understanding of the text.",
        "The response demonstrates a partial or literal understanding of the text.",
        "The response demonstrates an understanding of the complexities of the text.",
    ],
    5: [
        "The response is incorrect or irrelevant or contains insufficient information to demonstrate comprehension.",
        "The response is a minimal description of the mood created by the author. It includes little or no information from the memoir and may include misinterpretations.",
        "The response is a partial description of the mood created by the author. It includes limited information from the memoir and may include misinterpretations.",
        "The response is a mostly clear, complete, and accurate description of the mood created by the author. It includes relevant but often general information from the memoir.",
        "The response is a clear, complete, and accurate description of the mood created by the author. It includes relevant and specific information from the memoir.",
    ],
    6: [
        "The response is totally incorrect or irrelevant, or contains insufficient evidence to demonstrate comprehension.",
        "The response is a minimal description of the obstacles the builders faced. It includes little or no information from the excerpt and may include misinterpretations.",
        "The response is a partial description of the obstacles the builders faced. It includes limited information from the excerpt and may include misinterpretations.",
        "The response is a mostly clear, complete, and accurate description of the obstacles the builders faced. It includes relevant but often general information from the excerpt.",
        "The response is a clear, complete, and accurate description of the obstacles the builders faced. It includes relevant and specific information from the excerpt.",
    ],
}
_HOLISTIC[4] = list(_HOLISTIC[3])  # sets 3 and 4 share the reading-response rubric

# Trait rubrics. Set 7: four traits scored 0-3. Set 8: six traits scored 1-6.
TRAITS: Dict[int, Dict[str, List[str]]] = {
    7: {
        "ideas": [
            "Ideas are not focused on the task and/or are undeveloped.",
            "Tells a story with ideas that are minimally focused on the topic and developed with limited and/or general details.",
            "Tells a story with ideas that are somewhat focused on the topic and are developed with a mix of specific and/or general details.",
            "Tells a story with ideas that are clearly focused on the topic and are thoroughly developed with specific, relevant details.",
        ],
        "organization": [
            "No organization evident.",
            "Organization and connections between ideas and/or events are weak.",
            "Organization and connections between ideas and/or events are logically sequenced.",
            "Organization and connections between ideas and/or events are clear and logically sequenced.",
        ],
        "style": [
            "Ineffective use of language for the writer's purpose and audience.",
            "Limited use of language, including lack of variety in word choice and sentences, may hinder support for the writer's purpose and audience.",
            "Adequate command of language, including effective word choice and clear sentences, supports the writer's purpose and audience.",
            "Command of language, including effective and compelling word choice and varied sentence structure, clearly supports the writer's purpose and audience.",
        ],
        "conventions": [
            "Ineffective use of conventions of Standard English for grammar, usage, spelling, capitalization, and punctuation.",
            "Limited use of conventions of Standard English for grammar, usage, spelling, capitalization, and punctuation for the grade level.",
            "Adequate use of conventions of Standard English for grammar, usage, spelling, capitalization, and punctuation for the grade level.",
            "Consistent, appropriate use of conventions of Standard English for grammar, usage, spelling, capitalization, and punctuation for the grade level.",
        ],
    },
    8: {
        "ideas_and_content": [
            "The writing lacks a central idea or purpose. Ideas are extremely limited or simply unclear.",
            "Main ideas and purpose are somewhat unclear or development is attempted but minimal.",
            "The reader can understand the main ideas, although they may be overly broad or simplistic, and the results may not be effective. Supporting detail is often limited, insubstantial, overly general, or occasionally slightly off-topic.",
            "The writing is clear and focused. The reader can easily understand the main ideas. Support is present, although it may be limited or rather general.",
            "The writing is clear, focused and interesting. It holds the reader's attention. Main ideas stand out and are developed by supporting details suitable to audience and purpose.",
            "The writing is exceptionally clear, focused, and interesting. It holds the reader's attention throughout. Main ideas stand out and are developed by strong support and rich details suitable to audience and purpose.",
        ],
        "organization": [
            "The writing lacks coherence; organization seems haphazard and disjointed. Even after rereading, the reader remains confused.",
            "The writing lacks a clear organizational structure. An occasional organizational device is discernible; however, the writing is either difficult to follow or too short to demonstrate organizational skills.",
            "An attempt has been made to organize the writing; however, the overall structure is inconsistent or skeletal.",
            "Organization is clear and coherent. Order and structure are present, but may seem formulaic.",
            "The organization enhances the central idea(s) and its development. The order and structure are strong and move the reader through the text.",
            "The organization enhances the central idea(s) and its development. The order and structure are compelling and move the reader through the text easily.",
        ],
        "voice": [
            "The writing seems to lack a sense of involvement or commitment. No engagement of the writer; the writing is flat and lifeless.",
            "The writing provides little sense of involvement or commitment. There is no evidence that the writer has chosen a suitable voice.",
            "The writer's commitment to the topic seems inconsistent. A sense of the writer may emerge at times; however, the voice is either inappropriately personal or inappropriately impersonal.",
            "A voice is present. The writer seems committed to the topic, and there may be a sense of \"writing to be read.\" In places, the writing is expressive, engaging, or sincere.",
            "The writer has chosen a voice appropriate for the topic, purpose, and audience. The writer demonstrates commitment to the topic, and there is a sense of \"writing to be read.\"",
            "The writer has chosen a voice appropriate for the topic, purpose, and audience. The writer demonstrates deep commitment to the topic, and there is an exceptional sense of \"writing to be read.\"",
        ],
        "word_choice": [
            "The writing shows an extremely limited vocabulary or is so filled with misuses of words that the meaning is obscured.",
            "Language is monotonous and/or misused, detracting from the meaning and impact.",
            "Language lacks precision and variety, or may be inappropriate to audience and purpose in places. A sort of \"generic\" paper filled with familiar words and phrases.",
            "Words effectively convey the intended message. The writer employs a variety of words that are functional and appropriate to audience and purpose.",
            "Words convey the intended message in an interesting, precise, and natural way appropriate to audience and purpose. The writer employs a broad range of words carefully chosen for impact.",
            "Words convey the intended message in an exceptionally interesting, precise, and natural way. The writer employs a rich, broad range of words carefully chosen and thoughtfully placed for impact.",
        ],
        "sentence_fluency": [
            "The writing is difficult to follow or to read aloud. Sentences tend to be incomplete, rambling, or very awkward.",
            "The writing tends to be either choppy or rambling. Awkward constructions often force the reader to slow down or reread.",
            "The writing tends to be mechanical rather than fluid. Occasional awkward constructions may force the reader to slow down or reread.",
            "The writing flows; however, connections between phrases or sentences may be less than fluid. Sentence patterns are somewhat varied.",
            "The writing has an easy flow and rhythm. Sentences are carefully crafted, with strong and varied structure.",
            "The writing has an effective flow and rhythm. Sentences show a high degree of craftsmanship, with consistently strong and varied structure.",
        ],
        "conventions": [
            "Numerous errors in usage, spelling, capitalization, and punctuation repeatedly distract the reader and make the text difficult to read.",
            "The writing demonstrates little control of standard writing conventions. Frequent, significant errors impede readability.",
            "The writing demonstrates limited control of standard writing conventions. Errors begin to impede readability.",
            "The writing demonstrates control of standard writing conventions. Significant errors do not occur frequently. Minor errors do not impede readability.",
            "The writing demonstrates strong control of standard writing conventions and uses them effectively to enhance communication. Errors are few and minor.",
            "The writing demonstrates exceptionally strong control of standard writing conventions and uses them effectively to enhance communication. Errors are so few and so minor that the reader can easily skim right over them.",
        ],
    },
}

# Set 2 is scored on a second domain, Language Conventions (1-4), reported as domain2.
SET2_CONVENTIONS = [
    "Does the writing sample exhibit a minimal or less than minimal control of language skills? Errors are serious and numerous. The reader may need to stop and reread part of the sample and may struggle to discern the writer's meaning.",
    "Does the writing sample exhibit a fair control of language skills? Errors are typically frequent and may occasionally impede the flow of communication.",
    "Does the writing sample exhibit a good control of language skills? Errors are occasional and are often of the first-draft variety; they have a minor impact on the flow of communication.",
    "Does the writing sample exhibit a superior command of language skills? There are no errors that impair the flow of communication. Errors are generally of the first-draft variety or occur when the student attempts sophisticated sentence construction.",
]

# Rater-scale value of level index 0 (set 7 traits start at 0, set 8 traits at 1).
TRAIT_MIN = {7: 0, 8: 1}
# Rater-scale value of level index 0 for the holistic question.
HOLISTIC_MIN = {1: 1, 2: 1, 3: 0, 4: 0, 5: 0, 6: 0}
# Column index in the ASAP file: rater{r}_trait{TRAIT_COLUMNS[set][name]}.
TRAIT_COLUMNS = {
    7: {"ideas": 1, "organization": 2, "style": 3, "conventions": 4},
    8: {"ideas_and_content": 1, "organization": 2, "voice": 3, "word_choice": 4,
        "sentence_fluency": 5, "conventions": 6},
}
TRAIT_LABELS = {
    "holistic": "Holistic", "language_conventions": "Language Conventions",
    "ideas": "Ideas", "organization": "Organization", "style": "Style", "conventions": "Conventions",
    "ideas_and_content": "Ideas and Content", "voice": "Voice", "word_choice": "Word Choice",
    "sentence_fluency": "Sentence Fluency",
}


def questions_for(essay_set: int) -> Dict[str, dict]:
    """Kev /v1/systemone `questions` for one essay of this set."""
    task = PROMPTS[essay_set]
    qs: Dict[str, dict] = {}
    if essay_set in TRAITS:
        for name, levels in TRAITS[essay_set].items():
            qs[name] = {
                "type": "score",
                "instructions": (
                    f"A student wrote this essay for the prompt: \"{task}\" "
                    f"Rate the essay's {TRAIT_LABELS[name]} using the rubric."
                ),
                "criteria": levels,
            }
    else:
        qs["holistic"] = {
            "type": "score",
            "instructions": (
                f"A student wrote this essay for the prompt: \"{task}\" "
                "Score the essay using the rubric."
            ),
            "criteria": _HOLISTIC[essay_set],
        }
        if essay_set == 2:
            qs["language_conventions"] = {
                "type": "score",
                "instructions": (
                    f"A student wrote this essay for the prompt: \"{task}\" "
                    "Rate the essay's command of Language Conventions using the rubric."
                ),
                "criteria": SET2_CONVENTIONS,
            }
    return qs


def trait_rater_value(essay_set: int, level_index: float, question: str = "") -> float:
    """Kev level index -> the rater's scale for that question.

    Traits: set 7 0-3, set 8 1-6. Holistic: set 1-2 1-6, sets 3-6 from 0.
    Set 2 language conventions: 1-4.
    """
    if question == "holistic":
        return HOLISTIC_MIN[essay_set] + level_index
    if question == "language_conventions":
        return 1 + level_index
    return TRAIT_MIN[essay_set] + level_index


def to_domain1(essay_set: int, answers: Dict[str, float]) -> float:
    """Kev expected level indices -> the set's resolved (domain1) scale.

    Uses each set's adjudication rule with Kev standing in for both raters:
      1: sum of two raters (1-6 each)          -> 2 * (idx + 1)
      2: reader 1 is the score of record (1-6) -> idx + 1
      3-6: resolved = higher/agreed rater      -> idx
      7: per rater I + O + S + C (0-12), resolved = rater1 + rater2 -> 2 * (I+O+S+C).
         The set description says "Ideas (points doubled)" and a 0-15 range, but in
         training_set_rel3.tsv rater1_domain1 equals the plain trait sum for all 1,569
         essays (checked in tests/test_rubrics.py), so we follow the data.
      8: 2(I + O + S + C) + 2C with traits on 1-6
    """
    if essay_set == 1:
        return 2.0 * (answers["holistic"] + 1)
    if essay_set == 2:
        return answers["holistic"] + 1
    if essay_set in (3, 4, 5, 6):
        return answers["holistic"]
    if essay_set == 7:
        a = answers
        return 2.0 * (a["ideas"] + a["organization"] + a["style"] + a["conventions"])
    if essay_set == 8:
        t = {k: v + 1 for k, v in answers.items()}
        return 2.0 * (t["ideas_and_content"] + t["organization"] + t["sentence_fluency"] + t["conventions"]) + 2.0 * t["conventions"]
    raise ValueError(essay_set)
