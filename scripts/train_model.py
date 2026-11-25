"""Train one n-gram using an explicit development or fold-training partition."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ngram_models import CharacterNGramModel, WordNGramModel
from scripts.prepare_data import read_sources


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--family', choices=('word', 'character'), required=True)
    parser.add_argument('--n', type=int, choices=range(1, 11), required=True)
    parser.add_argument('--alpha', type=float, default=1.0)
    parser.add_argument('--manifest', type=Path, default=ROOT / 'data/manifest.json')
    parser.add_argument('--raw', type=Path, default=ROOT / 'data/raw')
    parser.add_argument('--fold', type=int, choices=range(1, 6))
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--prefix', default='pri')
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text())
    projects = manifest['development_projects']
    if args.fold is not None:
        projects = next(fold['train_projects'] for fold in manifest['folds'] if fold['fold'] == args.fold)
    model_class = WordNGramModel if args.family == 'word' else CharacterNGramModel
    model = model_class(args.n, args.alpha)
    model.fit(read_sources(args.manifest, projects, args.raw))
    model.save(args.output)
    restored = model_class.load(args.output)
    if restored.suggest(args.prefix) != model.suggest(args.prefix):
        raise RuntimeError('Saved model predictions differ after loading')
    print(json.dumps({'family': args.family, 'n': args.n, 'training_projects': projects,
                      'vocabulary_size': len(model.vocabulary), 'output': str(args.output),
                      'prefix': args.prefix, 'suggestions': restored.suggest(args.prefix)}, indent=2))


if __name__ == '__main__':
    main()
