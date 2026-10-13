# TODO

## Future renderer enhancements

- Support injection of custom block classes in `chunks2lines()`
- Allow custom blocks to provide their own layout behavior
- Preserve scroll anchoring and block identity for custom block types
- Maintain compatibility with existing block classes
- Fully decouple the renderer from yotsuba-cli

## Minor renderer adjustments

- Unicode-aware width calculation for the renderer
- Safer html parsing -> avoid escaped literal markup being interpreted as actual tags

## State & navigational enhancements

- Decouple generic navigation infrastructure from yotsuba-specific formatting behavior
- Change the state system so going to the same view you're currently in doesn't launch a new view
- (Unsure) Implement view stack based navigation

## Networking enhancements

- Implement more sophisticated networking behavior
- Make `api.py` fully 4chan api compliant

## Potential new features

- Show SFW/NSFW labels in `boards()`
- Smart status bar
    - Possible examples:
        - /board/ - title
        - /board/ No.123456 - Subject
        - /board/ No.123456 - 8 replies
- Visiting threads by their numeric post ID
- Page refresh for both index pages & individual threads
- Open index or thread in external browser

