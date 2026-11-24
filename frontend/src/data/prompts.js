// The eight ASAP prompts the grader was trained on (data/Essay_Set_Descriptions).
// The model only knows these prompts: an essay is scored against the human-scored
// essays written for the same prompt.
export const PROMPTS = [
  {
    id: 1,
    title: 'Computers and society',
    kind: 'Persuasive letter',
    grade: 8,
    scale: [2, 12],
    scaleNote: 'Two raters × 1–6',
    prompt:
      'More and more people use computers, but not everyone agrees that this benefits society. Those who support advances in technology believe that computers have a positive effect on people. Others are concerned that people are spending too much time on their computers and less time exercising, enjoying nature, and interacting with family and friends. Write a letter to your local newspaper in which you state your opinion on the effects computers have on people. Persuade the readers to agree with you.',
  },
  {
    id: 2,
    title: 'Censorship in libraries',
    kind: 'Persuasive essay',
    grade: 10,
    scale: [1, 6],
    scaleNote: 'Writing applications, 1–6',
    prompt:
      '“All of us can think of a book that we hope none of our children or any other children have taken off the shelf. But if I have the right to remove that book from the shelf — that work I abhor — then you also have exactly the same right and so does everyone else.” — Katherine Paterson. Write a persuasive essay to a newspaper reflecting your views on censorship in libraries. Should certain materials, such as books, music, movies, magazines, etc., be removed from the shelves if they are found offensive? Support your position with convincing arguments from your own experience, observations, and/or reading.',
  },
  {
    id: 3,
    title: 'Setting and the cyclist',
    kind: 'Response to a text',
    grade: 10,
    scale: [0, 3],
    scaleNote: 'Rubric 0–3',
    source: '“Rough Road Ahead: Do Not Exceed Posted Speed Limit” by Joe Kurmaskie',
    prompt:
      'Write a response that explains how the features of the setting affect the cyclist. In your response, include examples from the essay that support your conclusion.',
  },
  {
    id: 4,
    title: 'The ending of “Winter Hibiscus”',
    kind: 'Response to a text',
    grade: 10,
    scale: [0, 3],
    scaleNote: 'Rubric 0–3',
    source: '“Winter Hibiscus” by Minfong Ho',
    prompt:
      'Read the last paragraph of the story: “When they come back, Saeng vowed silently to herself, in the spring, when the snows melt and the geese return and this hibiscus is budding, then I will take that test again.” Write a response that explains why the author concludes the story with this paragraph. Include details and examples from the story that support your ideas.',
  },
  {
    id: 5,
    title: 'Mood of a memoir',
    kind: 'Response to a text',
    grade: 8,
    scale: [0, 4],
    scaleNote: 'Rubric 0–4',
    source: '“Narciso Rodriguez” from Home: The Blueprints of Our Lives',
    prompt:
      'Describe the mood created by the author in the memoir. Support your answer with relevant and specific information from the memoir.',
  },
  {
    id: 6,
    title: 'Docking dirigibles on the Empire State Building',
    kind: 'Response to a text',
    grade: 10,
    scale: [0, 4],
    scaleNote: 'Rubric 0–4',
    source: '“The Mooring Mast” by Marcia Amidon Lüsted',
    prompt:
      'Based on the excerpt, describe the obstacles the builders of the Empire State Building faced in attempting to allow dirigibles to dock there. Support your answer with relevant and specific information from the excerpt.',
  },
  {
    id: 7,
    title: 'A story about patience',
    kind: 'Narrative',
    grade: 7,
    scale: [0, 24],
    scaleNote: 'Two raters × four traits (0–3)',
    prompt:
      'Write about patience. Being patient means that you are understanding and tolerant. A patient person experiences difficulties without complaining. Do only one of the following: write a story about a time when you were patient OR write a story about a time when someone you know was patient OR write a story in your own way about patience.',
  },
  {
    id: 8,
    title: 'Laughter',
    kind: 'Narrative',
    grade: 10,
    scale: [0, 60],
    scaleNote: 'Composite of six traits (1–6)',
    prompt:
      'We all understand the benefits of laughter. For example, someone once said, “Laughter is the shortest distance between two people.” Many other people believe that laughter is an important part of any relationship. Tell a true story in which laughter was one element or part.',
  },
];

export const promptById = (id) => PROMPTS.find((p) => p.id === Number(id));
