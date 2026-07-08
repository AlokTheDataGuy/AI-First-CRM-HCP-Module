import { useDispatch } from 'react-redux'
import { setField } from '../store/interactionSlice'

// Renders a list field (attendees / materials / samples) as removable chips.
// The AI fills these via the chat; a manual "+ Add" is provided as a fallback.
export default function ChipList({
  field,
  items = [],
  placeholder,
  emptyText,
  addLabel = '+ Add',
}) {
  const dispatch = useDispatch() 

  const add = () => {
    const value = window.prompt(placeholder || `Add to ${field}`)
    if (value && value.trim()) {
      dispatch(setField({ field, value: [...items, value.trim()] }))
    }
  }

  const remove = (idx) => {
    dispatch(setField({ field, value: items.filter((_, i) => i !== idx) }))
  }

  return (
    <div className="chiplist">
      <div className="chiplist__items">
        {items.length === 0 && (
          <span className="chiplist__empty">{emptyText || placeholder || 'None'}</span>
        )}
        {items.map((item, i) => (
          <span className="chip" key={`${item}-${i}`}>
            {item}
            <button className="chip__x" onClick={() => remove(i)} aria-label="remove">
              ×
            </button>
          </span>
        ))}
      </div>
      <button className="btn btn--small" onClick={add}>
        {addLabel}
      </button>
    </div>
  )
}
