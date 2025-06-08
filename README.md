# What model and API provider should I use for this AI Meeting app?
Great question. There are a few constraints we should consider: cost, performance, speed, image understanding, and reasoning.

## Instantaneous Answers
For a live interview, getting near-instantaneous answers is going to be important. We'll want to use the Fast AI inference models. Cerebras is the fastest with Sambanova and Groq close behind.

Cost-wise both cerebras and groq have a free-tier with rate limits based on requests and tokens. Both are similar with a rate limit of 30/30000 requests/tokens per minute or more for Llama-4 Scout. Unless the interview is asking you a new question every 5 seconds you'll probably be fine.

However cerebras can't process images yet, so groq is the winner here.

Next, let's take a look at what models that Cerebras and groq have.
Cerebras: L4 Scout, L3.3 70B
Groq: L4 Scout, L4 Maverick, L3.3 70B, QwQ

L3.3 vs L4 Scout is a bit of a toss-up, but L4 Scout can do images. L4 Maverick on the free-tier has a much lower token limit.
QwQ is a reasoning model, but pales in comparison to other leading models like DeepSeek R1, Claude Sonnet, Gemini, o4-mini

Let's stick with groq - reasonably fast and has image support.

## Reasoning Models
Most of the leading models have image understanding and reasoning capabilities. 

Deepseek R1 is out because of no image support. You can Screenshot -> OCR -> Text to send to R1. But eh that's a lot of work for low payoff.

Performance-wise, it's a toss up between Gemini 2.5 Pro > Claude 4 Sonnet (Thinking) > o4 Mini. The order listed is the general consensus, but the benchmarks are relatively similar.

Cost-wise ($/1M output tokens): o4 Mini ($4.40) < Gemini 2.5 Pro ($10) < Claude 4 Sonnet ($15)
I'll probably use o4 Mini or Gemini 2.5 Pro here through OpenRouter. It's the easiest to get access to all these different models wrapped up in a nice package.

# Using this app in an interview
Pressing on a word during a live interview will send that word & all subsequent text to the backend. It will also record the word's index - this will become relevant later. The text is sent to a Fast AI Inference model to determine what question type it is: Trivia, Resume, Leetcode, SysDesign, Clarify. The classification may be improved with better prompts and examples.

Based on the classified question type, it will use a different prompt for the conversation. See prompts.py to fine-tune each prompt / prompt class. This prompt will be sent to the API Provider again and the response will be returned.
Frontend -> Backend -> API Provider conversation classification -> API Provider conversation + prompt -> response

If the classified question type is incorrect, you can use the buttons to send the intended question type. It will use the existing wordIndex to re-send the transcript beginning from that word.

## Question types and usage thought process
Trivia: Answer the trivia question and return an outline of the information. In the future, I'd like to add in web-search capability.

Resume: Adds the job description and resume in the context. Answer in STAR format.

Coding: Any coding or leetcode problem. Pairs well with the clarify prompt. Usually includes a screenshot/image of the screen and usually uses reasoning mode.

SysDesign: Any system design problem. Pairs well with the clarify prompt. Might include a screenshot and might use reasoning mode.

Clarify: It's unlikely that a question will be classified as this, but it has a few neat functions. First it generates a list of clarifying questions. It then analyzes those clarifications with respect to the system you're designing or the coding question. Things like the CAP Theorem, database scaling, monolith vs distributed systems, whether to use a hashmap, etc. Get these questions answered by the interviewer first before re-prompting with the relevant coding & system design buttons. 

Since the wordIndex is saved, you can easily just re-press the button with the relevant switches (image & reasoning). I need to test to see if how I talk in the interview helps format the information in a more easily understandable way.

# Usage
Get a GPU with 8gb of spare VRAM (or a second gpu leggo leggo)

Rename example_config.yaml -> config.yaml and configure the api keys and models. 

The models I selected are my preference.  

In Hugging Face, accept all user conditions for pyannote mentioned in the TL;DR https://github.com/pyannote/pyannote-audio

The API keys are fake, but I think it's funny to leave it in for scrapers to find and fail.

# TODO & New Features
There must be a more efficient way to send the transcript via websocket - instead of sending the entire transcript, only send the last chunk being updated and put a chunk_id to denote order.

Add RAG for all question types: previously asked questions, relevant projects, past stories, labuladong's FUCKING ALGORITHM notes, system design docs, etc.

Use python multiprocessing > multithreading & asyncio so new requests aren't blocked by the GIL.
Or is there a way to add more cores for the backend without blocking?

Add web-search capabilities to trivia (searxng, beautifulsoup)

Update the frontend and backend to allow streaming. This is important for reasoning models that take time to spit out an answer.

PyAudio is brittle AF - explore alternatives

## QoL code cleanup
POST /meetings/1/tags - uses a tag name in the data to add a tag to a meeting. Instead pass in the tag_id. Adjust the backend accordingly.

Split settings into a separate router

Throw the backend schemas into the same file. Probably do the same on the frontend lib/api. This is a shitty web app, not a production grade application.

## Other features
Use a whisper server instead of whisper library directly. It adds startup overhead, but can more easily process parallel requests. Furthermore only load diarization when needed. And/or look for a less VRAM intensive alternative.
- nemo branch uses nvidia parakeet, which is arguably better than whisper - but it's also fast and performant AF. This branch also loads diarization when needed
- whisper_server is adapted to use a whisper_server running on localhost:8081 - However it feels slower than using python whisper. Later changes with async and non-blocking post requests has improved the performance, but eh keep it simple, stupid. Probably just stick with the whisper library.

## Will you support new changes?
![Image](dontCare.png)

# GO FORTH AND VIBE CODE YOUR WAY TO A JOB

# Misc Information
## LLM Inference API Providers
### Fast AI Inference
Cerebras
https://inference-docs.cerebras.ai/introduction
https://inference-docs.cerebras.ai/support/pricing

Sambanova
https://docs.sambanova.ai/cloud/docs/get-started/supported-models
https://docs.sambanova.ai/cloud/docs/get-started/rate-limits

Groq
https://console.groq.com/docs/models
https://console.groq.com/docs/rate-limits

Parasail
https://www.saas.parasail.io/pricing

### Leading Model Providers
Google
https://ai.google.dev/gemini-api/docs/pricing

OpenAI
https://platform.openai.com/docs/models
https://platform.openai.com/docs/pricing

Anthropic
https://docs.anthropic.com/en/docs/about-claude/pricing

OpenRouter
https://openrouter.ai/models