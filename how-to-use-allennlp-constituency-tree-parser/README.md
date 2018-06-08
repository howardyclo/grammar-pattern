# How to use AllenNLP Constituency Tree Parser
Here, we will show you how to extract constituency tree string for sentences step-by-step.

## 0. Setup a Python virtual environment (Optional)
We recommend you to install dependencies in Python virtual environment (Python 3.x). We use *Anaconda* for package management. See [simple tutorial](https://uoa-eresearch.github.io/eresearch-cookbook/recipe/2014/11/20/conda/) for usage.

```sh
$ conda create -n grammar-pattern python=3 anaconda

$ conda activate grammar-pattern

$ conda install pip
```

## 1. Clone the **modified** AllenNLP GitHub repository and install dependencies
We only return constituency tree string from the original version of constituency tree parser instead of the other unwanted data (it's very huge!). We save our modification to the `grammar-pattern` branch, so **please remember to switch to the `grammar-pattern` branch before running the parser**.
```sh
$ git clone https://github.com/howardyclo/allennlp.git

$ git checkout grammar-pattern

$ pip install -r requirements.txt
```

## 2. Make a simple input file
The input format for AllenNLP's model requires **jsonline** format. For example, if you need to parse a text file like:
```
This is the first sentence .
This is the second sentence .
This is the third sentence .
```

You need to convert them to lines of JSON object:
```json
{"sentence": "This is the first sentence ."}
{"sentence": "This is the second sentence ."}
{"sentence": "This is the third sentence ."}
```

Now, let's test a single sentence as input!
```sh
$ echo '{"sentence": "He likes to discuss the issues ."}' > sample.input.jsonl
```

## 3. Run constituency tree parser

On CPU:
```sh
$ python -m allennlp.run predict \
https://s3-us-west-2.amazonaws.com/allennlp/models/elmo-constituency-parser-2018.03.14.tar.gz \
sample.input.jsonl \
--predictor=constituency-parser \
--output-file sample.output.txt
```

On GPU:
```sh
$ python -m allennlp.run predict \
https://s3-us-west-2.amazonaws.com/allennlp/models/elmo-constituency-parser-2018.03.14.tar.gz \
sample.input.jsonl \
--predictor=constituency-parser \
--output-file sample.output.txt \
--batch-size 32 \
--cuda-device 0
```
Output from terminal (add `--silent` without printing message to the terminal):
```
input:  {'sentence': 'He likes to discuss the issues .'}
prediction:  "(S (NP (PRP He)) (VP (VBZ likes) (S (VP (TO to) (VP (VB discuss) (NP (DT the) (NNS issues)))))) (. .))"
```
Output from output file:
```
"(S (NP (PRP He)) (VP (VBZ likes) (S (VP (TO to) (VP (VB discuss) (NP (DT the) (NNS issues)))))) (. .))"
```

See more about the [arguments](https://allenai.github.io/allennlp-docs/api/allennlp.commands.predict.html).