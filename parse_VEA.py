import pdfplumber
import re
import csv


def parse_data_line(line):
    """Parse a single data line into a dictionary with student information."""
    tokens = line.split()
    icva_id = tokens[0]

    # Identify the test date using a regex pattern
    date_pattern = r"\d{2}-[A-Z]{3}-\d{4}"
    date_index = next(
        i for i, token in enumerate(tokens) if re.match(date_pattern, token)
    )

    # Extract full name (all tokens between ICVA ID and test date)
    name_tokens = tokens[1:date_index]
    full_name = " ".join(name_tokens)

    # Extract test date and scores
    test_date = tokens[date_index]
    scores = tokens[date_index + 1 :]

    # Validate that we have exactly 7 scores
    if len(scores) != 7:
        raise ValueError(f"Expected 7 scores, got {len(scores)} in line: {line}")

    return {
        "ICVA ID": icva_id,
        "Full Name": full_name,
        "Test Date": test_date,
        "Scale Score": scores[0],  # Total Test (scale)
        "Total Percent Correct": scores[1],  # Total Test (percent correct)
        "Anatomy": scores[2],
        "Physiology": scores[3],
        "Pharmacology": scores[4],
        "Microbiology": scores[5],
        "Pathology": scores[6],
    }


def main():
    """Main function to parse the PDF and save data to CSV."""
    pdf_path = "pdf/veamay2025_westernuniversity_icva044.PDF"

    # Extract text from all pages of the PDF
    with pdfplumber.open(pdf_path) as pdf:
        full_text = ""
        for page in pdf.pages:
            full_text += page.extract_text() + "\n"

    # Split text into lines and filter data lines starting with 'ICVA'
    lines = full_text.splitlines()
    data_lines = [line.strip() for line in lines if line.strip().startswith("ICVA")]

    # Parse each data line
    parsed_rows = []
    for line in data_lines:
        try:
            row = parse_data_line(line)
            parsed_rows.append(row)
        except Exception as e:
            print(f"Error parsing line: {line}\n{e}")

    # Verify the number of students
    expected_students = 107
    if len(parsed_rows) != expected_students:
        print(
            f"Warning: Expected {expected_students} students, but parsed {len(parsed_rows)}."
        )
    else:
        print(f"Successfully parsed {len(parsed_rows)} students.")

    # Save to CSV
    output_file = "parsed_data.csv"
    with open(output_file, "w", newline="") as csvfile:
        fieldnames = [
            "ICVA ID",
            "Full Name",
            "Test Date",
            "Scale Score",
            "Total Percent Correct",
            "Anatomy",
            "Physiology",
            "Pharmacology",
            "Microbiology",
            "Pathology",
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in parsed_rows:
            writer.writerow(row)

    print(f"Data saved to {output_file}")


if __name__ == "__main__":
    main()
