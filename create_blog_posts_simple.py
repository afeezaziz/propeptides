#!/usr/bin/env python3
"""
Simple script to create blog posts without importing the app directly
"""

import os
import sys
import sqlite3
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_blog_posts():
    """Create blog posts about semaglutide, retatrutide, and their comparison"""

    # Database path
    db_path = 'peptides.db'

    # Check if database exists
    if not os.path.exists(db_path):
        print(f"Database {db_path} not found. Please run the application first to create the database.")
        return

    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if blog_posts table exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='blog_post'
        """)

        if not cursor.fetchone():
            print("Blog posts table not found. Creating it...")
            cursor.execute("""
                CREATE TABLE blog_post (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title VARCHAR(200) NOT NULL,
                    slug VARCHAR(200) NOT NULL UNIQUE,
                    content TEXT NOT NULL,
                    excerpt TEXT,
                    featured_image VARCHAR(500),
                    author_id INTEGER,
                    status VARCHAR(20) DEFAULT 'published',
                    published_at DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

        # Blog posts data
        blog_posts = [
            {
                'title': 'Semaglutide: The Revolutionary GLP-1 Receptor Agonist',
                'slug': 'semaglutide-revolutionary-glp-1-receptor-agonist',
                'content': '''# Semaglutide: The Revolutionary GLP-1 Receptor Agonist

## Introduction

Semaglutide has emerged as one of the most significant breakthroughs in metabolic health and weight management in recent years. As a glucagon-like peptide-1 (GLP-1) receptor agonist, it has transformed the treatment landscape for type 2 diabetes and obesity.

## What is Semaglutide?

Semaglutide is a synthetic analog of human GLP-1, a hormone that plays a crucial role in glucose metabolism and appetite regulation. Developed by Novo Nordisk, it mimics the effects of natural GLP-1 but with enhanced stability and longer duration of action.

### Chemical Structure and Mechanism

The molecular structure of semaglutide has been modified to resist degradation by dipeptidyl peptidase-4 (DPP-4) enzymes, allowing it to remain active in the body for up to a week. This modification includes:
- Amino acid substitution at position 8 (alanine to alpha-aminoisobutyric acid)
- Attachment of a C-18 fatty diacid chain via a linker
- These modifications enable albumin binding and prolonged half-life

## Mechanism of Action

Semaglutide works through multiple pathways:

### 1. Glucose-Dependent Insulin Secretion
- Stimulates insulin release from pancreatic beta cells
- Only when blood glucose levels are elevated
- Reduces risk of hypoglycemia

### 2. Glucagon Suppression
- Suppresses glucagon secretion from alpha cells
- Reduces hepatic glucose production
- Contributes to better glycemic control

### 3. Gastric Emptying
- Slows gastric emptying
- Increases satiety
- Reduces postprandial glucose excursions

### 4. Central Nervous System Effects
- Acts on GLP-1 receptors in the brain
- Reduces appetite and food intake
- May have neuroprotective effects

## Clinical Applications

### Type 2 Diabetes Management
- HbA1c reduction of 1.5-2.0%
- Weight loss of 4-6 kg on average
- Cardiovascular risk reduction
- Once-weekly dosing improves compliance

### Weight Management
- FDA-approved for chronic weight management
- Average weight loss of 15-20% in clinical trials
- Significant improvement in metabolic parameters
- Dosed at 2.4 mg weekly for weight loss

## Cardiovascular Benefits

Semaglutide has demonstrated remarkable cardiovascular benefits:
- Reduced major adverse cardiovascular events (MACE) by 26%
- Improved cardiovascular outcomes in high-risk patients
- Beneficial effects on blood pressure and lipid profile
- Potential direct cardioprotective effects

## Dosing and Administration

### Type 2 Diabetes
- Starting dose: 0.25 mg once weekly
- Maintenance dose: 1.0 mg once weekly
- Subcutaneous injection
- Can be taken at any time of day

### Weight Management
- Starting dose: 0.25 mg once weekly
- Target dose: 2.4 mg once weekly
- Gradual dose escalation to minimize side effects

## Side Effects and Safety Profile

### Common Side Effects
- Gastrointestinal effects (nausea, vomiting, diarrhea)
- Usually mild to moderate and transient
- Decrease in incidence over time

### Serious Considerations
- Risk of pancreatitis (rare)
- Gallbladder-related events
- Potential thyroid C-cell tumor risk (contraindicated in MEN2)
- Diabetic retinopathy complications in some patients

## Research and Future Directions

Ongoing research is exploring:
- Oral formulations for improved convenience
- Potential applications in neurodegenerative diseases
- Cardiovascular protection mechanisms
- Combination therapies for enhanced efficacy

## Conclusion

Semaglutide represents a significant advancement in metabolic health management. Its dual benefits on glycemic control and weight loss, combined with proven cardiovascular benefits, make it a valuable therapeutic option. As research continues, we may discover even more applications for this remarkable peptide.

## References

1. Wilding JP, et al. Once-weekly semaglutide in adults with overweight or obesity. N Engl J Med. 2021;384:989-1002.
2. Marso SP, et al. Semaglutide and cardiovascular outcomes in patients with type 2 diabetes. N Engl J Med. 2016;375:1834-1844.
3. Davies MJ, et al. Efficacy of liraglutide for weight loss among patients with type 2 diabetes. Lancet. 2015;385:1095-1105.
''',
                'excerpt': 'Comprehensive guide to semaglutide, a revolutionary GLP-1 receptor agonist for diabetes and weight management.',
                'featured_image': 'https://images.unsplash.com/photo-1587854692152-cbe660dbde88?w=800&h=400&fit=crop',
                'status': 'published',
                'published_at': datetime.now().isoformat()
            },
            {
                'title': 'Retatrutide: The Next Generation Triple Hormone Receptor Agonist',
                'slug': 'retatrutide-next-generation-triple-hormone-receptor-agonist',
                'content': '''# Retatrutide: The Next Generation Triple Hormone Receptor Agonist

## Introduction

Retatrutide represents the cutting edge of peptide therapeutics, emerging as a novel triple hormone receptor agonist that targets GLP-1, GIP, and glucagon receptors simultaneously. Developed by Eli Lilly, this investigational peptide has shown unprecedented efficacy in clinical trials for weight management and metabolic health.

## What is Retatrutide?

Retatrutide (LY3437943) is a first-in-class triple agonist that activates three key metabolic hormone receptors:
- GLP-1 (glucagon-like peptide-1) receptor
- GIP (glucose-dependent insulinotropic polypeptide) receptor
- Glucagon receptor

This multi-target approach represents a significant advancement beyond single and dual receptor agonists currently available.

## Molecular Structure and Design

The peptide structure of retatrutide has been engineered to:
- Maintain high affinity for all three target receptors
- Resist enzymatic degradation
- Enable once-weekly dosing
- Optimize pharmacokinetic profile

### Key Structural Features
- Modified amino acid sequence for enhanced stability
- Site-specific fatty acid modification for prolonged action
- Optimized receptor binding domains

## Mechanism of Action

Retatrutide's triple agonism creates a synergistic effect on metabolism:

### 1. GLP-1 Receptor Agonism
- Enhances glucose-dependent insulin secretion
- Suppresses glucagon release
- Slows gastric emptying
- Promotes satiety through central nervous system effects

### 2. GIP Receptor Agonism
- Potentiates insulin secretion
- Enhances adipose tissue metabolism
- May have direct effects on bone metabolism
- Complements GLP-1 effects on glucose homeostasis

### 3. Glucagon Receptor Agonism
- Increases energy expenditure
- Promotes fat oxidation (lipolysis)
- Enhances hepatic metabolism
- May contribute to weight loss through thermogenesis

## Clinical Trial Results

### Phase 2 Trial Results
The TRIPLE-REDUCE trial demonstrated remarkable efficacy:
- **Weight Loss**: Up to 24% weight loss at 48 weeks (12 mg dose)
- **Glycemic Control**: HbA1c reduction of 2.0-2.5%
- **Metabolic Improvements**: Significant improvements in lipid profile, blood pressure
- **Dose Response**: Clear dose-dependent effects across all endpoints

### Comparison to Existing Therapies
Retatrutide has shown superior efficacy compared to:
- GLP-1 receptor agonists alone (semaglutide, liraglutide)
- Dual GIP/GLP-1 receptor agonists (tirzepatide)
- Traditional weight loss medications

## Potential Benefits and Applications

### Weight Management
- Unprecedented weight loss efficacy
- Potential for treating severe obesity
- May reduce need for bariatric surgery
- Sustainable weight maintenance potential

### Type 2 Diabetes
- Superior glycemic control
- Weight loss as primary benefit
- Potential cardiovascular benefits
- Beta-cell preservation effects

### Cardiovascular Risk Reduction
- Improved lipid profiles
- Blood pressure reduction
- Anti-inflammatory effects
- Direct cardiovascular protection

## Safety and Tolerability

### Common Side Effects
- Gastrointestinal effects (nausea, vomiting, diarrhea)
- Generally mild to moderate
- Dose-dependent incidence
- Often transient and resolve with continued use

### Safety Considerations
- Ongoing monitoring for cardiovascular events
- Potential for gallbladder-related events
- Theoretical risk of pancreatitis
- Long-term safety data still emerging

## Dosing and Administration

### Current Development Status
- Once-weekly subcutaneous injection
- Dose escalation protocol to minimize side effects
- Maintenance doses ranging from 8-12 mg weekly
- Flexible dosing schedule

## Future Research Directions

### Phase 3 Trials
- Large-scale cardiovascular outcome trials
- Long-term safety and efficacy studies
- Comparative effectiveness research
- Quality of life assessments

### Potential New Indications
- Non-alcoholic steatohepatitis (NASH)
- Cardiovascular disease prevention
- Neurodegenerative disorders
- Metabolic syndrome components

## Market Impact and Availability

### Regulatory Status
- Currently in Phase 3 clinical trials
- Potential FDA approval timeline: 2025-2026
- European Medicines Agency review parallel to FDA
- Global launch strategy being developed

### Market Position
- Potential to become best-in-class obesity treatment
- Premium pricing expected given superior efficacy
- May capture significant market share from existing therapies
- Insurance coverage considerations ongoing

## Conclusion

Retatrutide represents a paradigm shift in metabolic disease treatment. Its triple receptor agonism approach has demonstrated unprecedented efficacy in clinical trials, potentially offering superior outcomes compared to existing therapies. While long-term safety data is still emerging, the initial results are highly promising.

## References

1. Jastreboff AM, et al. Triple-hormone-receptor agonist retatrutide for obesity. N Engl J Med. 2023;389:1255-1267.
2. Frias JP, et al. Efficacy and safety of retatrutide in type 2 diabetes. Lancet. 2023;402:1039-1051.
3. Carmichael S, et al. Triple receptor agonism in metabolic disease: Mechanisms and clinical potential. Nat Rev Endocrinol. 2023;19:451-463.
''',
                'excerpt': 'Comprehensive analysis of retatrutide, a groundbreaking triple hormone receptor agonist showing unprecedented weight loss results.',
                'featured_image': 'https://images.unsplash.com/photo-1536304993881-37690a892438?w=800&h=400&fit=crop',
                'status': 'published',
                'published_at': datetime.now().isoformat()
            },
            {
                'title': 'Semaglutide vs Retatrutide: A Comprehensive Comparison of GLP-1 Based Therapies',
                'slug': 'semaglutide-vs-retatrutide-comprehensive-comparison',
                'content': '''# Semaglutide vs Retatrutide: A Comprehensive Comparison of GLP-1 Based Therapies

## Introduction

The landscape of metabolic health and weight management has been revolutionized by the emergence of advanced peptide therapeutics. Semaglutide and retatrutide represent two significant milestones in this evolution, offering different approaches to treating type 2 diabetes and obesity. This comprehensive comparison examines their mechanisms, efficacy, safety profiles, and clinical applications.

## Overview and Development Status

### Semaglutide
- **Developer**: Novo Nordisk
- **Approval Status**: FDA approved (2017 for diabetes, 2021 for weight management)
- **Brand Names**: Ozempic®, Wegovy®, Rybelsus®
- **Market Status**: Widely available globally
- **Clinical Experience**: Extensive real-world data since 2017

### Retatrutide
- **Developer**: Eli Lilly
- **Approval Status**: Phase 3 clinical trials
- **Market Status**: Investigational, not yet approved
- **Clinical Experience**: Limited to trial data
- **Projected Availability**: 2025-2026

## Mechanism of Action Comparison

### Semaglutide: Single Receptor Agonism
Semaglutide is a selective GLP-1 receptor agonist that works through:
- **Primary Target**: GLP-1 receptors only
- **Glucose Control**: Enhanced insulin secretion, suppressed glucagon
- **Weight Effects**: Appetite suppression, delayed gastric emptying
- **Cardiovascular**: Proven cardiovascular benefits

### Retatrutide: Triple Receptor Agonism
Retatrutide activates three key metabolic receptors:
- **Primary Targets**: GLP-1, GIP, and glucagon receptors
- **Glucose Control**: Multi-hormonal approach to insulin/glucagon balance
- **Weight Effects**: Appetite suppression + increased energy expenditure
- **Metabolic**: Enhanced fat oxidation and thermogenesis

## Efficacy Comparison

### Weight Loss Results

| Treatment | Trial Duration | Weight Loss | Patient Population |
|-----------|----------------|-------------|-------------------|
| Semaglutide 2.4 mg | 68 weeks | 14.9-17.4% | STEP trials (obesity) |
| Retatrutide 12 mg | 48 weeks | 24.2% | TRIPLE-REDUCE (obesity) |
| Semaglutide 1.0 mg | 30 weeks | 4-6% | SUSTAIN trials (T2D) |
| Retatrutide 8-12 mg | 36 weeks | 17-22% | T2D trials |

### Glycemic Control

| Parameter | Semaglutide | Retatrutide |
|-----------|-------------|-------------|
| HbA1c Reduction | 1.5-2.0% | 2.0-2.5% |
| Fasting Glucose | Significant reduction | Greater reduction |
| Postprandial Glucose | Controlled | Superior control |
| Insulin Resistance | Improved | Markedly improved |

### Cardiovascular Effects

| Endpoint | Semaglutide | Retatrutide |
|-----------|-------------|-------------|
| MACE Reduction | 26% (proven) | Theoretical benefit |
| Blood Pressure | Moderate reduction | Significant reduction |
| Lipid Profile | Modest improvement | Substantial improvement |
| Heart Failure | Potential benefit | Unknown |

## Safety and Tolerability

### Common Side Effects

| Side Effect | Semaglutide Incidence | Retatrutide Incidence |
|-------------|----------------------|-----------------------|
| Nausea | 20-44% | 30-50% |
| Vomiting | 10-24% | 15-30% |
| Diarrhea | 15-30% | 20-35% |
| Constipation | 10-20% | 15-25% |

### Serious Adverse Events

| Concern | Semaglutide | Retatrutide |
|---------|-------------|-------------|
| Pancreatitis | Rare (0.1-0.3%) | Theoretical risk |
| Gallbladder Events | 1-3% | Unknown (monitoring) |
| Thyroid C-cell Tumors | Contraindicated | Likely contraindicated |
| Diabetic Retinopathy | 3-4% (in T2D) | Unknown |

## Dosing and Administration

### Semaglutide
- **Starting Dose**: 0.25 mg weekly
- **Target Dose**: 1.0 mg (diabetes) or 2.4 mg (weight)
- **Dose Escalation**: 4-8 weeks to target
- **Administration**: Subcutaneous injection
- **Timing**: Any time of day

### Retatrutide
- **Starting Dose**: 2-4 mg weekly
- **Target Dose**: 8-12 mg weekly
- **Dose Escalation**: 8-16 weeks to target
- **Administration**: Subcutaneous injection
- **Timing**: Flexible scheduling

## Cost and Accessibility

### Current Market Position
- **Semaglutide**: $1,000-1,400 monthly, insurance coverage varies
- **Retatrutide**: Estimated $1,500-2,000 monthly (projected)

### Insurance Coverage
- **Semaglutide**: Covered for diabetes, limited for obesity
- **Retatrutide**: Coverage details pending approval

## Patient Selection Considerations

### Semaglutide Candidates
- Type 2 diabetes patients
- Moderate obesity (BMI ≥30)
- Patients with established cardiovascular disease
- Those needing proven long-term safety data

### Potential Retatrutide Candidates
- Severe obesity (BMI ≥35-40)
- Patients inadequate on current therapies
- Those needing maximum weight loss
- Research participants in clinical trials

## Future Development

### Semaglutide Evolution
- Oral formulations (already available)
- Cardiovascular indication expansion
- Combination therapies
- Generic/biosimilar development

### Retatrutide Development
- Phase 3 trial completion (2024-2025)
- Regulatory submissions (2025-2026)
- Real-world evidence collection
- Next-generation triple agonists

## Clinical Decision Making

### When to Choose Semaglutide
- Need for proven, established therapy
- Cardiovascular risk reduction priority
- Insurance coverage considerations
- Preference for long-term safety data

### When to Consider Retatrutide (Future)
- Maximum weight loss requirement
- Inadequate response to current therapies
- Severe obesity with complications
- Access through clinical trials

## Conclusion

Both semaglutide and retatrutide represent significant advances in metabolic health treatment. Semaglutide offers proven efficacy with extensive real-world experience, while retatrutide promises unprecedented weight loss through its innovative triple receptor approach.

The choice between these therapies will depend on:
- Individual patient needs and goals
- Comorbid conditions and risk factors
- Insurance coverage and accessibility
- Risk tolerance and safety considerations

As the field continues to evolve, we may see these therapies used sequentially or in combination, offering personalized treatment approaches for metabolic disease.

## References

1. Wilding JP, et al. Once-weekly semaglutide in adults with overweight or obesity. N Engl J Med. 2021;384:989-1002.
2. Jastreboff AM, et al. Triple-hormone-receptor agonist retatrutide for obesity. N Engl J Med. 2023;389:1255-1267.
3. Davies M, et al. Long-term outcomes with GLP-1 receptor agonists. Lancet Diabetes Endocrinol. 2023;11:234-246.
4. Rubino D, et al. Comparative effectiveness of metabolic therapies. JAMA. 2023;329:1123-1135.
''',
                'excerpt': 'Detailed comparison of semaglutide and retatrutide, examining efficacy, safety, and clinical applications of these groundbreaking peptide therapies.',
                'featured_image': 'https://images.unsplash.com/photo-1576091160550-2173dba999ef?w=800&h=400&fit=crop',
                'status': 'published',
                'published_at': datetime.now().isoformat()
            }
        ]

        # Insert blog posts
        for post_data in blog_posts:
            try:
                cursor.execute("""
                    INSERT INTO blog_post
                    (title, slug, content, excerpt, featured_image, status, published_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    post_data['title'],
                    post_data['slug'],
                    post_data['content'],
                    post_data['excerpt'],
                    post_data['featured_image'],
                    post_data['status'],
                    post_data['published_at']
                ))
                print(f"Created blog post: {post_data['title']}")
            except sqlite3.IntegrityError as e:
                print(f"Blog post already exists or error: {e}")

        # Commit changes
        conn.commit()
        print("\nBlog posts created successfully!")

        # Display summary
        cursor.execute("SELECT COUNT(*) FROM blog_post")
        total_posts = cursor.fetchone()[0]
        print(f"Total blog posts in database: {total_posts}")

    except Exception as e:
        print(f"Error creating blog posts: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    create_blog_posts()