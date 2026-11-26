import { BarChart } from "echarts/charts";
import { GridComponent, LegendComponent, TooltipComponent } from "echarts/components";
import * as echarts from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import { useEffect, useRef } from "react";
import type { WeeklyCount } from "../types";
import { formatWeek } from "../utils/format";

echarts.use([BarChart, GridComponent, LegendComponent, TooltipComponent, CanvasRenderer]);

// Design tokens (docs/00): blue for opened, accent green for merged. The legend carries
// the meaning in words, and the same numbers are available as a table.
const OPENED = "#255DB3";
const MERGED = "#087F6D";
const INK = "#172B35";
const MUTED = "#52656E";
const BORDER = "#E1E6E9";

type Props = { weekly: WeeklyCount[] };

// Loaded on demand (React.lazy) so the chart library stays out of the main bundle.
export default function WeeklyChart({ weekly }: Props) {
  const container = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!container.current) return;
    const chart = echarts.init(container.current);
    chart.setOption({
      color: [OPENED, MERGED],
      textStyle: { fontFamily: "Inter, system-ui, sans-serif", color: MUTED },
      grid: { left: 8, right: 8, top: 40, bottom: 8, containLabel: true },
      legend: { top: 0, left: 0, textStyle: { color: INK }, icon: "roundRect" },
      tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
      xAxis: {
        type: "category",
        data: weekly.map((week) => formatWeek(week.week_start)),
        axisLine: { lineStyle: { color: BORDER } },
        axisTick: { show: false },
      },
      yAxis: {
        type: "value",
        minInterval: 1,
        splitLine: { lineStyle: { color: BORDER } },
      },
      series: [
        { name: "Opened", type: "bar", data: weekly.map((week) => week.opened), barMaxWidth: 24 },
        { name: "Merged", type: "bar", data: weekly.map((week) => week.merged), barMaxWidth: 24 },
      ],
    });
    const onResize = () => chart.resize();
    window.addEventListener("resize", onResize);
    return () => {
      window.removeEventListener("resize", onResize);
      chart.dispose();
    };
  }, [weekly]);

  return <div ref={container} className="chart-canvas" />;
}
