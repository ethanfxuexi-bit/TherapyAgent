import {
  forwardRef,
  useCallback,
  useImperativeHandle,
  useRef,
  useState,
} from 'react'
import { Stage, Layer, Line } from 'react-konva'
import type Konva from 'konva'
import { Eraser, Pen, RotateCcw, RotateCw, Trash2 } from 'lucide-react'

export interface DrawingCanvasHandle {
  exportImage: () => Promise<Blob | null>
  isEmpty: () => boolean
  clear: () => void
}

interface LineData {
  tool: 'pen' | 'eraser'
  points: number[]
  color: string
  size: number
}

interface Props {
  width: number
  height: number
}

const COLORS = ['#1e293b', '#ef4444', '#f59e0b', '#22c55e', '#3b82f6', '#8b5cf6', '#ec4899']

export const DrawingCanvas = forwardRef<DrawingCanvasHandle, Props>(function DrawingCanvas(
  { width, height },
  ref,
) {
  const [lines, setLines] = useState<LineData[]>([])
  const [history, setHistory] = useState<LineData[][]>([[]])
  const [historyStep, setHistoryStep] = useState(0)
  const [tool, setTool] = useState<'pen' | 'eraser'>('pen')
  const [color, setColor] = useState(COLORS[0])
  const [brushSize, setBrushSize] = useState(4)
  const isDrawing = useRef(false)
  const stageRef = useRef<Konva.Stage>(null)

  const pushHistory = useCallback(
    (newLines: LineData[]) => {
      const next = history.slice(0, historyStep + 1)
      next.push(newLines)
      setHistory(next)
      setHistoryStep(next.length - 1)
    },
    [history, historyStep],
  )

  const handlePointerDown = (e: Konva.KonvaEventObject<PointerEvent>) => {
    e.evt.preventDefault()
    isDrawing.current = true
    const stage = e.target.getStage()
    const pos = stage?.getPointerPosition()
    if (!pos) return

    const newLine: LineData = {
      tool,
      points: [pos.x, pos.y],
      color: tool === 'eraser' ? '#ffffff' : color,
      size: tool === 'eraser' ? brushSize * 2 : brushSize,
    }
    setLines([...lines, newLine])
  }

  const handlePointerMove = (e: Konva.KonvaEventObject<PointerEvent>) => {
    if (!isDrawing.current) return
    e.evt.preventDefault()
    const stage = e.target.getStage()
    const point = stage?.getPointerPosition()
    if (!point) return

    const lastLine = lines[lines.length - 1]
    if (!lastLine) return
    lastLine.points = lastLine.points.concat([point.x, point.y])
    setLines([...lines.slice(0, -1), lastLine])
  }

  const handlePointerUp = () => {
    if (isDrawing.current) {
      isDrawing.current = false
      pushHistory(lines)
    }
  }

  const undo = () => {
    if (historyStep <= 0) return
    const prev = historyStep - 1
    setHistoryStep(prev)
    setLines(history[prev])
  }

  const redo = () => {
    if (historyStep >= history.length - 1) return
    const next = historyStep + 1
    setHistoryStep(next)
    setLines(history[next])
  }

  const clear = () => {
    setLines([])
    pushHistory([])
  }

  useImperativeHandle(ref, () => ({
    exportImage: async () => {
      const stage = stageRef.current
      if (!stage) return null
      const uri = stage.toDataURL({ pixelRatio: 2 })
      const res = await fetch(uri)
      return res.blob()
    },
    isEmpty: () => lines.length === 0,
    clear,
  }))

  return (
    <div className="flex flex-col gap-3">
      <div
        className="flex flex-wrap items-center gap-2 p-2 rounded-xl bg-slate-50 dark:bg-slate-800/50"
        role="toolbar"
        aria-label="Drawing tools"
      >
        <button
          onClick={() => setTool('pen')}
          className={`p-2 rounded-lg ${tool === 'pen' ? 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/50' : 'hover:bg-slate-200 dark:hover:bg-slate-700'}`}
          aria-label="Pen tool"
          aria-pressed={tool === 'pen'}
        >
          <Pen size={18} />
        </button>
        <button
          onClick={() => setTool('eraser')}
          className={`p-2 rounded-lg ${tool === 'eraser' ? 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/50' : 'hover:bg-slate-200 dark:hover:bg-slate-700'}`}
          aria-label="Eraser tool"
          aria-pressed={tool === 'eraser'}
        >
          <Eraser size={18} />
        </button>

        <div className="w-px h-6 bg-slate-200 dark:bg-slate-600 mx-1" aria-hidden />

        {COLORS.map((c) => (
          <button
            key={c}
            onClick={() => { setColor(c); setTool('pen') }}
            className={`w-6 h-6 rounded-full border-2 ${color === c && tool === 'pen' ? 'border-indigo-500 scale-110' : 'border-transparent'}`}
            style={{ backgroundColor: c }}
            aria-label={`Color ${c}`}
          />
        ))}

        <div className="w-px h-6 bg-slate-200 dark:bg-slate-600 mx-1" aria-hidden />

        <label className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-300">
          <span className="sr-only">Brush size</span>
          <input
            type="range"
            min={2}
            max={20}
            value={brushSize}
            onChange={(e) => setBrushSize(Number(e.target.value))}
            className="w-20 accent-indigo-500"
            aria-valuetext={`${brushSize} pixels`}
          />
        </label>

        <div className="w-px h-6 bg-slate-200 dark:bg-slate-600 mx-1" aria-hidden />

        <button onClick={undo} disabled={historyStep <= 0} className="p-2 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-700 disabled:opacity-30" aria-label="Undo">
          <RotateCcw size={18} />
        </button>
        <button onClick={redo} disabled={historyStep >= history.length - 1} className="p-2 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-700 disabled:opacity-30" aria-label="Redo">
          <RotateCw size={18} />
        </button>
        <button onClick={clear} className="p-2 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-700 text-red-500" aria-label="Clear canvas">
          <Trash2 size={18} />
        </button>
      </div>

      <div
        className="rounded-xl overflow-hidden border border-slate-200 dark:border-slate-700 shadow-sm touch-none"
        style={{ width, height }}
      >
        <Stage
          ref={stageRef}
          width={width}
          height={height}
          onPointerDown={handlePointerDown}
          onPointerMove={handlePointerMove}
          onPointerUp={handlePointerUp}
          onPointerLeave={handlePointerUp}
          style={{ background: '#ffffff', cursor: tool === 'eraser' ? 'cell' : 'crosshair' }}
        >
          <Layer>
            {lines.map((line, i) => (
              <Line
                key={i}
                points={line.points}
                stroke={line.color}
                strokeWidth={line.size}
                tension={0.4}
                lineCap="round"
                lineJoin="round"
              />
            ))}
          </Layer>
        </Stage>
      </div>
    </div>
  )
})
