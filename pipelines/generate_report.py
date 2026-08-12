import argparse
from jobs.report import generate_report

def main():    
	parser = argparse.ArgumentParser(description="Generate a city weather report.")
	parser.add_argument("city_name", help="City name stored in city_data.city_name")
	parser.add_argument(
		"--output",
		help="Optional HTML output path."
	)
	args = parser.parse_args()

	html_path = generate_report(args.city_name, args.output)
	print(f"HTML report: {html_path}")

if __name__ == "__main__":
    main()