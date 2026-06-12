"""
Module for interactive visualization of simulation results using Plotly.
Includes age pyramids, population trends, and household statistics.
"""

from typing import Dict, List
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd


class SimulationVisualizer:
    """
    Handles visualization of simulation results.
    
    Attributes:
        yearly_stats: Dictionary of yearly statistics from simulation
    """
    
    def __init__(self, yearly_stats: Dict[int, Dict]) -> None:
        """
        Initialize the visualizer.
        
        Args:
            yearly_stats: Dictionary mapping year numbers to statistics dictionaries
        """
        self.yearly_stats = yearly_stats
    
    def plot_interactive_age_pyramid(
        self,
        output_file: str = "age_pyramid_interactive.html"
    ) -> None:
        """
        Create an interactive demographic age pyramid (GUS style) for the final year.
        
        Features:
        - Males on the left (negative values)
        - Females on the right (positive values)
        - 5-year age groups from 0-4 to 85-89, then 90-94, 95-99, 100+
        - Dark blue for males, dark red for females
        - Symmetric X-axis around zero
        - Minimalist style matching official statistics
        
        Args:
            output_file: Path to save the HTML file
        """
        years = sorted(self.yearly_stats.keys())
        
        if not years:
            print("No data to visualize")
            return
        
        # Use final year for static pyramid
        final_year = years[-1]
        pyramid = self.yearly_stats[final_year]["age_pyramid"]
        
        # Sort age bins correctly (0-4, 5-9, ..., 85-89, 90-94, 95-99, 100+)
        age_order = []
        for start in range(0, 90, 5):
            age_order.append(f"{start}-{start+4}")
        
        # Extract data
        males = []
        females = []
        for age_bin in age_order:
            if age_bin in pyramid:
                males.append(-pyramid[age_bin]["male"])  # Negative for left side
                females.append(pyramid[age_bin]["female"])
            else:
                males.append(0)
                females.append(0)
        
        # Create figure
        fig = go.Figure()
        
        # Add male bars (left side, negative)
        fig.add_trace(go.Bar(
            y=age_order,
            x=males,
            name="Mężczyźni",
            orientation="h",
            marker_color="#1f77b4",  # Dark blue
            hovertemplate="<b>%{y}</b><br>Mężczyźni: %{value}<extra></extra>",
            showlegend=True,
        ))
        
        # Add female bars (right side, positive)
        fig.add_trace(go.Bar(
            y=age_order,
            x=females,
            name="Kobiety",
            orientation="h",
            marker_color="#d62728",  # Dark red
            hovertemplate="<b>%{y}</b><br>Kobiety: %{value}<extra></extra>",
            showlegend=True,
        ))
        
        # Calculate symmetric x-axis limits
        max_val = max(max(abs(x) for x in males), max(abs(x) for x in females))
        x_limit = max_val * 1.1  # Add 10% padding
        
        fig.update_layout(
            title={
                "text": f"<b>Piramida wieku populacji – rok {final_year} symulacji</b>",
                "x": 0.5,
                "xanchor": "center",
                "font": {"size": 18}
            },
            xaxis_title="Liczba osób",
            yaxis_title="Grupy wieku",
            barmode="overlay",
            height=700,
            width=1000,
            hovermode="closest",
            plot_bgcolor="white",
            paper_bgcolor="white",
            xaxis=dict(
                zeroline=True,
                zerolinewidth=2,
                zerolinecolor="black",
                range=[-x_limit, x_limit],
                showgrid=True,
                gridwidth=1,
                gridcolor="lightgray",
            ),
            yaxis=dict(
                showgrid=False,
            ),
            font=dict(family="Arial, sans-serif", size=12),
            legend=dict(
                x=0.5,
                y=-0.12,
                xanchor="center",
                yanchor="top",
                orientation="h",
                bgcolor="rgba(255, 255, 255, 0.8)",
                bordercolor="lightgray",
                borderwidth=1,
            ),
            margin=dict(l=100, r=100, b=120, t=120),
        )
        
        fig.write_html(output_file)
        print(f"Piramida wieku zapisana do {output_file}")
    
    def create_animated_age_pyramid(
        self,
        output_file: str = "piramida_wieku_animowana.html"
    ) -> None:
        """
        Create an animated demographic age pyramid with year slider.
        
        Features:
        - Interactive slider for year selection (0-50)
        - Smooth transitions between years
        - Dynamic title with current year
        - Same GUS style as static pyramid
        
        Args:
            output_file: Path to save the HTML file
        """
        years = sorted(self.yearly_stats.keys())
        
        if not years:
            print("No data to visualize")
            return
        
        # Age bin order
        age_order = []
        for start in range(0, 90, 5):
            age_order.append(f"{start}-{start+4}")
        
        # Prepare data for all years
        all_data = {}
        for year in years:
            pyramid = self.yearly_stats[year]["age_pyramid"]
            males = []
            females = []
            for age_bin in age_order:
                if age_bin in pyramid:
                    males.append(-pyramid[age_bin]["male"])
                    females.append(pyramid[age_bin]["female"])
                else:
                    males.append(0)
                    females.append(0)
            all_data[year] = {"males": males, "females": females}
        
        # Calculate symmetric x-axis limits across all years
        max_val = 0
        for year in years:
            males = all_data[year]["males"]
            females = all_data[year]["females"]
            max_val = max(max_val, max(abs(x) for x in males), max(abs(x) for x in females))
        x_limit = max_val * 1.1
        
        # Create initial figure with first year
        first_year = years[0]
        data = all_data[first_year]
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            y=age_order,
            x=data["males"],
            name="Mężczyźni",
            orientation="h",
            marker_color="#1f77b4",
            hovertemplate="<b>%{y}</b><br>Mężczyźni: %{value}<extra></extra>",
        ))
        
        fig.add_trace(go.Bar(
            y=age_order,
            x=data["females"],
            name="Kobiety",
            orientation="h",
            marker_color="#d62728",
            hovertemplate="<b>%{y}</b><br>Kobiety: %{value}<extra></extra>",
        ))
        
        # Create frames for animation
        frames = []
        for year in years:
            data = all_data[year]
            frames.append(go.Frame(
                data=[
                    go.Bar(y=age_order, x=data["males"], marker_color="#1f77b4"),
                    go.Bar(y=age_order, x=data["females"], marker_color="#d62728"),
                ],
                name=str(year),
                layout=go.Layout(
                    title_text=f"<b>Piramida wieku populacji – rok {year} symulacji</b>"
                )
            ))
        
        fig.frames = frames
        
        # Create slider
        sliders = [
            {
                "active": 0,
                "yanchor": "top",
                "y": -0.15,
                "xanchor": "left",
                "x": 0.1,
                "len": 0.8,
                "transition": {"duration": 300},
                "pad": {"b": 10, "t": 10},
                "currentvalue": {
                    "prefix": "Rok symulacji: ",
                    "visible": True,
                    "xanchor": "center",
                    "font": {"size": 16}
                },
                "steps": [
                    {
                        "args": [
                            [str(year)],
                            {
                                "frame": {"duration": 300, "redraw": True},
                                "mode": "immediate",
                                "transition": {"duration": 300},
                            }
                        ],
                        "method": "animate",
                        "label": str(year),
                    }
                    for year in years
                ],
            }
        ]
        
        fig.update_layout(
            title={
                "text": f"<b>Piramida wieku populacji – rok {first_year} symulacji</b>",
                "x": 0.5,
                "xanchor": "center",
                "font": {"size": 18}
            },
            xaxis_title="Liczba osób",
            yaxis_title="Grupy wieku",
            barmode="overlay",
            height=750,
            width=1000,
            hovermode="closest",
            plot_bgcolor="white",
            paper_bgcolor="white",
            sliders=sliders,
            xaxis=dict(
                zeroline=True,
                zerolinewidth=2,
                zerolinecolor="black",
                range=[-x_limit, x_limit],
                showgrid=True,
                gridwidth=1,
                gridcolor="lightgray",
            ),
            yaxis=dict(
                showgrid=False,
            ),
            font=dict(family="Arial, sans-serif", size=12),
            legend=dict(
                x=0.5,
                y=-0.08,
                xanchor="center",
                yanchor="top",
                orientation="h",
                bgcolor="rgba(255, 255, 255, 0.8)",
                bordercolor="lightgray",
                borderwidth=1,
            ),
            margin=dict(l=100, r=100, b=180, t=120),
        )
        
        fig.write_html(output_file)
        print(f"Animowana piramida wieku zapisana do {output_file}")
    
    def plot_population_trends(
        self,
        output_file: str = "population_trends.html"
    ) -> None:
        """
        Create line plot showing population trends over time.
        
        Args:
            output_file: Path to save the HTML file
        """
        years = sorted(self.yearly_stats.keys())
        populations = [self.yearly_stats[y]["total_population"] for y in years]
        multimorbidity = [self.yearly_stats[y].get("multimorbidity_count", 0) for y in years]
        avg_disability = [self.yearly_stats[y].get("average_disability_score", 0) for y in years]
        
        fig = make_subplots(
            rows=3, cols=1,
            subplot_titles=("Total Population", "Multimorbidity Cases", "Average Disability Score"),
            specs=[[{"secondary_y": False}], [{"secondary_y": False}], [{"secondary_y": False}]],
        )
        
        # Population
        fig.add_trace(
            go.Scatter(
                x=years, y=populations,
                mode="lines+markers",
                name="Population",
                line=dict(color="blue", width=2),
                hovertemplate="Year %{x}: %{y} people<extra></extra>",
            ),
            row=1, col=1,
        )
        
        # Multimorbidity
        fig.add_trace(
            go.Scatter(
                x=years, y=multimorbidity,
                mode="lines+markers",
                name="Multimorbidity",
                line=dict(color="red", width=2),
                hovertemplate="Year %{x}: %{y} cases<extra></extra>",
            ),
            row=2, col=1,
        )
        
        # Avg Disability
        fig.add_trace(
            go.Scatter(
                x=years, y=avg_disability,
                mode="lines+markers",
                name="Avg Disability",
                line=dict(color="orange", width=2),
                hovertemplate="Year %{x}: %{y:.3f}<extra></extra>",
            ),
            row=3, col=1,
        )
        
        fig.update_xaxes(title_text="Year", row=3, col=1)
        fig.update_yaxes(title_text="Count", row=1, col=1)
        fig.update_yaxes(title_text="Count", row=2, col=1)
        fig.update_yaxes(title_text="Score", row=3, col=1)
        
        fig.update_layout(
            height=800,
            title_text="<b>Population Trends Over 50 Years</b>",
            showlegend=False,
            hovermode="x unified",
            plot_bgcolor="rgba(240,240,240,0.5)",
        )
        
        fig.write_html(output_file)
        print(f"Population trends saved to {output_file}")
    
    def plot_households_trends(
        self,
        output_file: str = "households_trends.html"
    ) -> None:
        """
        Create line plot showing household trends over time.
        
        Args:
            output_file: Path to save the HTML file
        """
        years = sorted(self.yearly_stats.keys())
        households = [self.yearly_stats[y]["num_households"] for y in years]
        avg_size = [self.yearly_stats[y]["average_household_size"] for y in years]
        
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=("Number of Households", "Average Household Size"),
            vertical_spacing=0.12,
        )
        
        # Households
        fig.add_trace(
            go.Scatter(
                x=years, y=households,
                mode="lines+markers",
                name="Households",
                line=dict(color="green", width=2),
                fill="tozeroy",
                hovertemplate="Year %{x}: %{y} households<extra></extra>",
            ),
            row=1, col=1,
        )
        
        # Avg household size
        fig.add_trace(
            go.Scatter(
                x=years, y=avg_size,
                mode="lines+markers",
                name="Avg Size",
                line=dict(color="purple", width=2),
                hovertemplate="Year %{x}: %{y:.2f} members<extra></extra>",
            ),
            row=2, col=1,
        )
        
        fig.update_xaxes(title_text="Year", row=2, col=1)
        fig.update_yaxes(title_text="Count", row=1, col=1)
        fig.update_yaxes(title_text="Size", row=2, col=1)
        
        fig.update_layout(
            height=700,
            title_text="<b>Household Dynamics Over 50 Years</b>",
            showlegend=False,
            hovermode="x unified",
            plot_bgcolor="rgba(240,240,240,0.5)",
        )
        
        fig.write_html(output_file)
        print(f"Household trends saved to {output_file}")
    
    def plot_gender_distribution(
        self,
        output_file: str = "gender_distribution.html"
    ) -> None:
        """
        Create plot showing male/female distribution over time.
        
        Args:
            output_file: Path to save the HTML file
        """
        years = sorted(self.yearly_stats.keys())
        males = [self.yearly_stats[y]["num_males"] for y in years]
        females = [self.yearly_stats[y]["num_females"] for y in years]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=years, y=males,
            mode="lines+markers",
            name="Male",
            line=dict(color="lightblue", width=2),
            fill="tozeroy",
            hovertemplate="Year %{x}: %{y} males<extra></extra>",
        ))
        
        fig.add_trace(go.Scatter(
            x=years, y=females,
            mode="lines+markers",
            name="Female",
            line=dict(color="lightpink", width=2),
            fill="tozeroy",
            hovertemplate="Year %{x}: %{y} females<extra></extra>",
        ))
        
        fig.update_layout(
            title="<b>Gender Distribution Over Time</b>",
            xaxis_title="Year",
            yaxis_title="Population",
            hovermode="x unified",
            height=600,
            plot_bgcolor="rgba(240,240,240,0.5)",
        )
        
        fig.write_html(output_file)
        print(f"Gender distribution saved to {output_file}")
    
    def generate_all_plots(self, output_dir: str = ".") -> None:
        """
        Generate all visualization plots.
        
        Args:
            output_dir: Directory to save HTML files (default: current directory)
        """
        print("\nGenerating interactive visualizations...")
        self.plot_interactive_age_pyramid(f"{output_dir}/piramida_wieku_rok_50.html")
        self.create_animated_age_pyramid(f"{output_dir}/piramida_wieku_animowana.html")
        self.plot_population_trends(f"{output_dir}/population_trends.html")
        self.plot_households_trends(f"{output_dir}/households_trends.html")
        self.plot_gender_distribution(f"{output_dir}/gender_distribution.html")
        print("All visualizations generated successfully!")
