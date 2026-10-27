---
title: "Titanic Dataset — Exploratory Data Analysis"
description: "Exploratory analysis of Titanic passenger data, focusing on survival patterns, passenger class, sex, age, fares, and data quality."
date: 2025-07-23
featured: false
categories:
  - Python
  - Data Analysis
  - Visualization
---

# Titanic Dataset — Exploratory Data Analysis

<small>Python · pandas · Matplotlib · Seaborn · Jupyter Notebook</small>

## Summary

An exploratory data analysis of Titanic passenger records, using descriptive statistics and visualizations to examine data quality and explore how survival rates vary across passenger groups. The analysis focuses on passenger class, sex, age, ticket fare, family-related fields, and port of embarkation.

**Research question:** Which passenger characteristics show the clearest associations with survival in this dataset, and what limitations should be considered when interpreting the results?

## The dataset

The working dataset contains **1,309 passenger records** after removing one completely empty row, with 14 columns describing passenger class, survival status, name, sex, age, family relationships aboard, ticket, fare, cabin, embarkation port, lifeboat, body recovery, and destination. Not all fields are complete.

## Approach

- Inspected the dataset structure, data types, duplicate records, and missing values.
- Removed one completely empty row and filled one missing fare with the mean fare for third-class passengers.
- Compared descriptive statistics and survival rates across passenger classes.
- Explored survival patterns by sex, age group, and embarkation port.
- Used histograms, bar charts, scatter plots, correlation matrices, and boxplots to inspect distributions, relationships, and potential outliers.

## Main findings

- **Survival rates differed by passenger class:** 61.9% in first class, 43.0% in second class, and 25.5% in third class.
- **Sex was strongly associated with survival in this dataset.** Survival rates for women were about 96.5% in first class, 88.7% in second class, and 49.1% in third class. For men, the corresponding rates were about 34.1%, 14.6%, and 15.2%.
- Among passengers with a recorded age who were under 18, the observed survival rate was about 86.7% in first class, 87.9% in second class, and 36.8% in third class.
- Ticket fares varied considerably, especially in first class, and the fare distributions included high-value outliers.
- The dataset has substantial missingness in several columns: age is missing for 263 records, cabin for 1,014, lifeboat for 823, body number for 1,188, and destination for 564. These limitations affect how much can be inferred from each analysis.

## Limitations

This is an exploratory analysis, not a trained classification model. The notebook does not estimate predictive accuracy or establish causal relationships. Missing values remain in most affected columns; analyses use the records available for the variables involved. One missing third-class fare was imputed using that class's mean, which should be kept in mind when interpreting fare statistics. Correlations and group differences describe patterns in this dataset but do not prove why those patterns occurred.

## View the results and source

- [Open the HTML report](files/Titanic_EDA_report.html)
- [Download the PDF report](files/Titanic_EDA_report.pdf)
- [Download the notebook, dataset, images, and requirements](files/titanic_EDA_source.zip)

To run the notebook locally, place the original CSV file named `26__titanic.csv` in the same directory as the notebook. Required Python libraries include pandas, Matplotlib, Seaborn, and Jupyter.
