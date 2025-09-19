#!/usr/bin/env python3
"""
Script to create blog posts using uv and MySQL database
"""

import os
import sys
import pymysql
from datetime import datetime
import uuid

def generate_slug(title):
    """Generate URL-friendly slug from title"""
    return title.lower().replace(' ', '-').replace('_', '-').replace('?', '').replace('!', '').replace('.', '').replace(',', '')

def create_blog_posts():
    """Create blog posts about semaglutide and retatrutide"""

    # Database configuration
    db_config = {
        'host': '104.248.150.75',
        'port': 33004,
        'user': 'mariadb',
        'password': '0cZ0FRFBB1UPsmnTKjGfm8iofaBkb0s7JZAggtz1f3RGnqqnu7d2h6dk6zF8EGbv',
        'database': 'default',
        'charset': 'utf8mb4',
        'cursorclass': pymysql.cursors.DictCursor
    }

    try:
        # Connect to the database
        print("Connecting to MySQL database...")
        conn = pymysql.connect(**db_config)
        cursor = conn.cursor()

        # Check if post table exists (it should be 'post' based on models.py)
        cursor.execute("""
            SELECT TABLE_NAME
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'post'
        """, (db_config['database'],))

        if not cursor.fetchone():
            print("Post table not found. Creating it...")
            cursor.execute("""
                CREATE TABLE post (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    title VARCHAR(200) NOT NULL,
                    slug VARCHAR(200) NOT NULL UNIQUE,
                    content LONGTEXT NOT NULL,
                    excerpt TEXT,
                    featured_image VARCHAR(500),
                    author_id INT NOT NULL,
                    status VARCHAR(20) DEFAULT 'published',
                    meta_title VARCHAR(200),
                    meta_description TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (author_id) REFERENCES user(id)
                )
            """)
            conn.commit()
            print("Post table created successfully!")

        # Check if admin user exists, create if not
        cursor.execute("SELECT id FROM user WHERE email = 'admin@propeptides.com'")
        admin_user = cursor.fetchone()

        if not admin_user:
            print("Creating admin user...")
            cursor.execute("""
                INSERT INTO user (google_id, email, name, role, is_active, created_at, last_login, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                'admin_001',
                'admin@propeptides.com',
                'Propeptides Admin',
                'admin',
                True,
                datetime.now(),
                datetime.now(),
                datetime.now()
            ))
            conn.commit()
            # Get the auto-generated ID
            cursor.execute("SELECT LAST_INSERT_ID() as id")
            admin_user_id = cursor.fetchone()['id']
            print(f"Created admin user with ID: {admin_user_id}")
        else:
            admin_user_id = admin_user['id']

        # Blog posts data
        blog_posts = [
            {
                'title': 'Understanding Semaglutide: The Revolutionary GLP-1 Receptor Agonist',
                'slug': 'understanding-semaglutide-revolutionary-glp1-receptor-agonist',
                'content': '''# Understanding Semaglutide: The Revolutionary GLP-1 Receptor Agonist

## Introduction

Semaglutide has emerged as one of the most significant breakthrough medications in recent years, initially developed for type 2 diabetes management and later approved for weight management. This GLP-1 receptor agonist has transformed the treatment landscape for metabolic disorders and offers promising applications in peptide research.

## What is Semaglutide?

Semaglutide is a synthetic analog of human glucagon-like peptide-1 (GLP-1), a naturally occurring hormone that plays a crucial role in glucose metabolism and appetite regulation. As a GLP-1 receptor agonist, semaglutide mimics the effects of GLP-1 but with enhanced stability and longer duration of action.

### Chemical Structure and Mechanism

The peptide consists of 31 amino acids and features several key modifications that enhance its therapeutic properties:

- **Fatty acid side chain**: Allows for albumin binding, extending half-life
- **Amino acid substitutions**: Protect against degradation by DPP-4 enzymes
- **Half-life**: Approximately 7 days, enabling once-weekly dosing

## Mechanism of Action

Semaglutide works through multiple mechanisms to achieve its therapeutic effects:

### 1. Glucose-Dependent Insulin Secretion
- Stimulates insulin release from pancreatic beta cells
- Only activates when blood glucose levels are elevated
- Reduces risk of hypoglycemia

### 2. Glucagon Suppression
- Decreases glucagon secretion from alpha cells
- Reduces hepatic glucose production
- Improves fasting and postprandial glucose levels

### 3. Gastric Emptying Delay
- Slows gastric emptying rate
- Promotes satiety and reduces food intake
- Contributes to weight loss effects

### 4. Central Nervous System Effects
- Acts on GLP-1 receptors in the hypothalamus
- Reduces appetite and food cravings
- May have neuroprotective effects

## Clinical Applications

### Type 2 Diabetes Management
Semaglutide has demonstrated superior efficacy in HbA1c reduction compared to other antidiabetic medications:

- **HbA1c reduction**: 1.5-2.0% reduction on average
- **Weight loss**: 4-6 kg average weight reduction
- **Cardiovascular benefits**: Reduced risk of major cardiovascular events

### Weight Management
In obesity treatment, semaglutide has shown remarkable results:

- **STEP trials**: 15-20% weight loss in clinical studies
- **Maintenance**: Sustained weight loss over 2+ years
- **Metabolic improvements**: Improved blood pressure, lipid profiles

## Research Applications

### Cardiovascular Research
- Investigation of cardioprotective mechanisms
- Studies on heart failure with preserved ejection fraction
- Exploration of anti-inflammatory effects

### Neurological Research
- Potential neuroprotective properties
- Investigation in Alzheimer's disease and Parkinson's
- Studies on cognitive function improvement

### Metabolic Syndrome
- Research on non-alcoholic fatty liver disease
- Investigation of polycystic ovary syndrome applications
- Studies on metabolic inflammation

## Dosage and Administration

### Standard Dosing Regimens
- **Ozempic®**: 0.25mg, 0.5mg, 1.0mg once weekly for diabetes
- **Wegovy®**: 2.4mg once weekly for weight management
- **Rybelsus®**: Oral formulation available

### Administration Guidelines
- Subcutaneous injection (except oral formulation)
- Can be administered at any time of day
- Compatible with or without food

## Safety Profile

### Common Side Effects
- Gastrointestinal symptoms (nausea, vomiting, diarrhea)
- Usually mild to moderate and transient
- Typically improve over time

### Serious Considerations
- Risk of pancreatitis (rare)
- Thyroid C-cell tumor risk (contraindicated in MEN2)
- Gallbladder-related events

## Future Research Directions

### Combination Therapies
- Investigation with other peptide hormones
- Study of synergistic effects with amylin analogs
- Exploration of GIP/GLP-1 dual agonists

### New Formulations
- Long-acting depot formulations
- Oral bioavailability improvements
- Alternative delivery systems

## Conclusion

Semaglutide represents a significant advancement in peptide-based therapeutics, demonstrating the potential of targeted receptor agonists in treating complex metabolic disorders. Its success has paved the way for next-generation multi-agonist peptides and continues to drive innovation in peptide research and development.

For researchers and healthcare providers, understanding semaglutide's mechanisms and effects provides valuable insights into the future of metabolic disease treatment and the broader applications of peptide therapeutics.

*Note: This article is for informational purposes only. Always consult with healthcare professionals for medical advice and treatment decisions.*''',
                'excerpt': 'Semaglutide has revolutionized treatment for type 2 diabetes and weight management. This comprehensive guide explores its mechanism, clinical applications, and research potential.',
                'featured_image': 'https://images.unsplash.com/photo-1587854692152-cbe660dbde88?w=800&h=400&fit=crop',
                'author_id': admin_user_id,
                'status': 'published',
                'meta_title': 'Semaglutide: Complete Guide to GLP-1 Receptor Agonist | Propeptides',
                'meta_description': 'Comprehensive guide to semaglutide, covering mechanism of action, clinical applications, dosing, and research potential for type 2 diabetes and weight management.'
            },
            {
                'title': 'Retatrutide: The Triple Agonist Peptide Reshaping Metabolic Medicine',
                'slug': 'retatrutide-triple-agonist-peptide-reshaping-metabolic-medicine',
                'content': '''# Retatrutide: The Triple Agonist Peptide Reshaping Metabolic Medicine

## Introduction

Retatrutide represents the next evolution in incretin-based therapies, emerging as a potent triple agonist that targets three key metabolic receptors: glucagon-like peptide-1 (GLP-1), glucose-dependent insulinotropic polypeptide (GIP), and glucagon receptors. This innovative approach has shown unprecedented efficacy in clinical trials, potentially surpassing current weight management medications.

## What is Retatrutide?

Retatrutide is a novel synthetic peptide designed to simultaneously activate three distinct receptors involved in metabolic regulation. This tri-agonist approach represents a significant advancement beyond single and dual agonist therapies currently available.

### Molecular Design
The peptide structure incorporates specific modifications that allow for:
- **Multi-receptor activation**: Balanced activity at GLP-1, GIP, and glucagon receptors
- **Extended half-life**: Approximately 6 days, enabling weekly dosing
- **Optimized receptor binding**: Engineered for maximal therapeutic effect

## Mechanism of Action

### Triple Receptor Activation
Retatrutide's unique mechanism involves simultaneous stimulation of:

#### 1. GLP-1 Receptor Activation
- Enhanced glucose-dependent insulin secretion
- Suppressed glucagon release
- Delayed gastric emptying
- Central appetite suppression

#### 2. GIP Receptor Activation
- Augmented insulin secretion
- Improved adipose tissue metabolism
- Enhanced lipid mobilization
- Potential anabolic effects on bone

#### 3. Glucagon Receptor Activation
- Increased energy expenditure
- Enhanced fat oxidation
- Improved hepatic metabolism
- Reduced liver fat

### Synergistic Effects
The combination of these three mechanisms creates powerful synergistic effects:
- **Enhanced weight loss**: Superior to single or dual agonists
- **Improved metabolic health**: Comprehensive metabolic improvement
- **Glucose homeostasis**: Multi-faceted glucose regulation

## Clinical Trial Results

### TRIUMPH Phase 2 Trial
The groundbreaking TRIUMPH trial demonstrated remarkable results:

#### Weight Loss Efficacy
- **Dose-dependent response**: 8% to 24% weight loss across dose ranges
- **High-dose results**: 24% weight loss at 12mg weekly dose
- **Sustained effects**: Continued weight loss over 48-week period
- **Plateau management**: No evidence of weight loss plateau

#### Metabolic Improvements
- **HbA1c reduction**: Significant improvements in glycemic control
- **Blood pressure**: Substantial reductions in systolic and diastolic BP
- **Lipid profile**: Improvements in cholesterol and triglycerides
- **Liver fat**: Reduction in hepatic steatosis

### Body Composition Changes
- **Fat mass reduction**: Preferential loss of adipose tissue
- **Lean mass preservation**: Better preservation compared to other weight loss medications
- **Visceral fat**: Significant reduction in harmful visceral adiposity

## Comparative Efficacy

### vs. Semaglutide
- **Weight loss**: 24% vs 15% at highest doses
- **Speed of onset**: More rapid initial weight loss
- **Metabolic effects**: Broader metabolic improvements

### vs. Tirzepatide
- **Additional mechanism**: Glucagon receptor activation
- **Energy expenditure**: Higher resting energy expenditure
- **Fat oxidation**: Enhanced fat utilization

## Potential Applications

### Obesity Treatment
Retatrutide shows particular promise for:
- **Severe obesity**: Higher efficacy in BMI 35+ patients
- **Treatment-resistant obesity**: Effective where other treatments fail
- **Metabolic syndrome**: Comprehensive metabolic improvement

### Type 2 Diabetes
- **Glycemic control**: Superior HbA1c reduction
- **Weight loss**: Dual benefit of glucose control and weight reduction
- **Beta-cell function**: Potential preservation of pancreatic function

### NAFLD/NASH
- **Liver fat reduction**: Significant decrease in hepatic steatosis
- **Inflammation reduction**: Anti-inflammatory effects on liver tissue
- **Fibrosis improvement**: Potential to reverse liver fibrosis

## Research Implications

### Peptide Engineering
Retatrutide's success validates several key principles in peptide design:
- **Multi-target approach**: Benefits of receptor polypharmacology
- **Balanced agonism**: Importance of receptor activation ratios
- **Structure optimization**: Impact of molecular modifications

### Future Development
The tri-agonist approach opens new avenues for:
- **Receptor combinations**: Exploration of other receptor combinations
- **Tissue targeting**: Organ-specific delivery systems
- **Personalized medicine**: Tailored receptor activation profiles

## Safety and Tolerability

### Common Side Effects
- **Gastrointestinal**: Nausea, vomiting, diarrhea (dose-dependent)
- **Transient nature**: Most side effects decrease over time
- **Management strategies**: Dose escalation improves tolerability

### Safety Considerations
- **Pancreatitis risk**: Monitoring required
- **Gallbladder events**: Increased risk similar to other weight loss medications
- **Cardiovascular safety**: Ongoing long-term studies

## Future Directions

### Phase 3 Development
- **Large-scale trials**: Ongoing TRIUMPH phase 3 program
- **Long-term safety**: Extended follow-up studies
- **Real-world evidence**: Post-marketing surveillance plans

### Combination Therapies
- **Amylin analogs**: Potential for quadruple agonist approaches
- **Other peptides**: Exploration of complementary mechanisms
- **Non-peptide agents**: Combination with small molecule therapies

## Conclusion

Retatrutide represents a paradigm shift in metabolic medicine, demonstrating the power of multi-target peptide therapeutics. Its unprecedented efficacy in weight loss and metabolic improvement suggests a new era in the treatment of obesity and related metabolic disorders.

For researchers and clinicians, retatrutide offers both a powerful therapeutic tool and insights into the future of peptide-based drug development. The success of this tri-agonist approach validates the strategy of targeting multiple metabolic pathways simultaneously and opens new possibilities for treating complex metabolic diseases.

As development continues, retatrutide may well become the new gold standard in weight management and metabolic health, potentially benefiting millions of patients worldwide.

*Note: This article is for informational purposes only. Retatrutide is still under investigation and not yet approved by regulatory agencies. Always consult with healthcare professionals for medical advice.*''',
                'excerpt': 'Retatrutide is a groundbreaking triple agonist peptide targeting GLP-1, GIP, and glucagon receptors. Learn about its unprecedented efficacy and potential to transform metabolic medicine.',
                'featured_image': 'https://images.unsplash.com/photo-1536304993881-37690a892438?w=800&h=400&fit=crop',
                'author_id': admin_user_id,
                'status': 'published',
                'meta_title': 'Retatrutide: Triple Agonist Peptide Guide | Propeptides',
                'meta_description': 'Comprehensive guide to retatrutide, the innovative triple agonist peptide targeting GLP-1, GIP, and glucagon receptors for metabolic disorders and weight management.'
            },
            {
                'title': 'Semaglutide vs Retatrutide: Comparative Analysis of Next-Generation Peptide Therapeutics',
                'slug': 'semaglutide-vs-retatrutide-comparative-analysis-next-generation-therapeutics',
                'content': '''# Semaglutide vs Retatrutide: Comparative Analysis of Next-Generation Peptide Therapeutics

## Introduction

The landscape of metabolic medicine has been transformed by the development of advanced peptide therapeutics, with semaglutide and retatrutide representing two significant milestones in this evolution. While semaglutide has established itself as a groundbreaking single-agonist therapy, retatrutide emerges as a next-generation triple-agonist with potentially superior efficacy. This comprehensive analysis compares these two innovative peptides across multiple dimensions.

## Overview and Classification

### Semaglutide: The Established GLP-1 Agonist
- **Classification**: Single-receptor agonist (GLP-1)
- **Approval Status**: FDA-approved for diabetes and weight management
- **Market Availability**: Commercially available (Ozempic®, Wegovy®, Rybelsus®)
- **Clinical Experience**: Extensive real-world data

### Retatrutide: The Emerging Triple Agonist
- **Classification**: Multi-receptor agonist (GLP-1 + GIP + Glucagon)
- **Approval Status**: Phase 3 clinical trials
- **Market Availability**: Investigational only
- **Clinical Experience**: Limited to trial data

## Mechanism of Action Comparison

### Single vs. Multi-Target Approach

#### Semaglutide's Focused Action
**GLP-1 Receptor Effects:**
- Glucose-dependent insulin secretion
- Glucagon suppression
- Gastric emptying delay
- Central appetite suppression

**Advantages:**
- Well-understood mechanism
- Predictable effects
- Extensive safety data

**Limitations:**
- Single pathway targeting
- Ceiling effect on efficacy
- Limited impact on energy expenditure

#### Retatrutide's Comprehensive Action
**Triple Receptor Effects:**
- **GLP-1**: Insulin secretion, appetite suppression
- **GIP**: Additional insulin enhancement, fat metabolism
- **Glucagon**: Energy expenditure, fat oxidation

**Advantages:**
- Multi-pathway targeting
- Synergistic effects
- No apparent efficacy ceiling

**Complexities:**
- More complex pharmacology
- Potential for varied responses
- Limited long-term data

## Efficacy Comparison

### Weight Loss Outcomes

#### Clinical Trial Results

| Metric | Semaglutide (STEP Trials) | Retatrutide (TRIUMPH Trial) |
|--------|---------------------------|-----------------------------|
| Max Weight Loss | 15-20% | 24% |
| Time to Max Effect | 68 weeks | 48 weeks |
| Weight Loss Velocity | Gradual | Rapid |
| Plateau Observation | Yes | No evidence at 48 weeks |

#### Patient Subgroups Analysis
**BMI Categories:**
- **Class I Obesity (30-35)**: Semaglutide 12%, Retatrutide 18%
- **Class II Obesity (35-40)**: Semaglutide 15%, Retatrutide 22%
- **Class III Obesity (40+)**: Semaglutide 18%, Retatrutide 24%

### Metabolic Improvements

#### Glycemic Control
**HbA1c Reduction:**
- Semaglutide: 1.5-2.0%
- Retatrutide: 2.0-2.5%

**Mechanistic Differences:**
- Semaglutide: Primarily GLP-1 mediated
- Retatrutide: GLP-1 + GIP dual insulin enhancement

#### Cardiovascular Effects
**Blood Pressure:**
- Semaglutide: 5-7 mmHg systolic reduction
- Retatrutide: 8-10 mmHg systolic reduction

**Lipid Profile:**
- Semaglutide: Moderate improvements
- Retatrutide: Significant improvements (glucagon effect)

## Safety and Tolerability

### Side Effect Profiles

#### Gastrointestinal Effects
**Semaglutide:**
- Nausea: 20-30%
- Vomiting: 10-15%
- Diarrhea: 15-20%

**Retatrutide:**
- Nausea: 30-40%
- Vomiting: 15-25%
- Diarrhea: 20-30%

#### Management Strategies
- **Dose escalation**: Both require gradual titration
- **Timing effects**: Retatrutide effects may be more pronounced initially
- **Long-term adaptation**: Both show improvement over time

### Serious Safety Concerns

#### Known Risks
**Semaglutide:**
- Pancreatitis: Rare but established risk
- Thyroid C-cell tumors: Contraindicated in MEN2
- Gallbladder disease: Increased risk

**Retatrutide:**
- Similar GLP-1 related risks expected
- Additional glucagon-related concerns being monitored
- Long-term cardiovascular safety under investigation

## Practical Considerations

### Administration and Dosing

#### Current Regimens
**Semaglutide:**
- Starting dose: 0.25mg weekly
- Maintenance: 0.5-2.4mg weekly
- Oral option available (Rybelsus®)

**Retatrutide:**
- Starting dose: 2mg weekly (investigational)
- Maintenance: 8-12mg weekly
- Injectable only (currently)

### Cost and Accessibility

#### Current Market Realities
**Semaglutide:**
- Insurance coverage: Widely covered
- Cost: $800-1200/month
- Generic status: Patent protected

**Retatrutide:**
- Insurance coverage: Not available (investigational)
- Cost: Unknown (likely premium pricing)
- Timeline: Potential approval 2025-2026

## Patient Selection Considerations

### Ideal Candidates

#### Semaglutide Best For:
- Type 2 diabetes patients
- Moderate weight loss goals (10-15%)
- Patients preferring established therapies
- Those needing oral option

#### Retatrutide Best For:
- Severe obesity (BMI 35+)
- Treatment-resistant obesity
- Patients needing maximum efficacy
- Research study participants

### Comorbid Condition Considerations

#### Cardiovascular Disease
- **Semaglutide**: Proven cardiovascular benefits
- **Retatrutide**: Theoretical benefits, unproven

#### NAFLD/NASH
- **Semaglutide**: Moderate liver fat reduction
- **Retatrutide**: Significant liver fat reduction (glucagon effect)

## Future Outlook

### Development Trajectories

#### Semaglutide Evolution
- Generic competition potential
- New formulations under investigation
- Combination therapies in development

#### Retatrutide Potential
- Phase 3 results expected 2024-2025
- Potential FDA approval 2025-2026
- Possible first-line status for severe obesity

### Market Impact

#### Treatment Paradigm Shifts
- **Current**: Semaglutide as gold standard
- **Future**: Potential tiered approach based on severity
- **Combination**: Sequential or concurrent use possibilities

#### Research Implications
- Validates multi-target approaches
- Encourages novel peptide development
- May redefine treatment success metrics

## Clinical Decision Making

### Treatment Algorithm Considerations

#### First-Line Therapy
- Type 2 diabetes: Semaglutide remains first choice
- Mild-moderate obesity: Semaglutide preferred
- Severe obesity: Consider retatrutide when available

#### Treatment Sequencing
- **Step-up approach**: Start with semaglutide, advance to retatrutide
- **Early intensive therapy**: Direct to retatrutide for severe cases
- **Combination therapy**: Future possibility under investigation

### Monitoring Requirements

#### Semaglutide Monitoring
- Standard metabolic panel
- Thyroid function tests
- Pancreatic enzymes

#### Retatrutide Monitoring
- Enhanced monitoring (investigational)
- Additional safety parameters
- Long-term outcome tracking

## Conclusion

The comparison between semaglutide and retatrutide represents the evolution of peptide therapeutics from single-target to multi-target approaches. While semaglutide has established itself as a transformative therapy, retatrutide's emergence suggests we're entering a new era of metabolic medicine with unprecedented efficacy potential.

For clinicians, the choice between these agents will depend on multiple factors including patient severity, comorbidities, treatment goals, and drug availability. The future may well involve a tiered approach where semaglutide serves as first-line therapy for many patients, while retatrutide becomes the preferred option for severe obesity and treatment-resistant cases.

For researchers, these compounds validate both the effectiveness of GLP-1-based therapies and the potential of multi-target approaches. The success of retatrutide's triple-agonist strategy opens new avenues for peptide development and may lead to even more sophisticated multi-receptor targeting strategies.

As the field continues to evolve, both semaglutide and retatrutide will play crucial roles in reshaping our approach to metabolic disease treatment, offering hope to millions of patients affected by obesity, type 2 diabetes, and related metabolic disorders.

*Note: This article is for informational purposes only. Retatrutide is still under investigation. Always consult with healthcare professionals for treatment decisions.*''',
                'excerpt': 'Comprehensive comparison of semaglutide vs retatrutide, analyzing efficacy, safety, mechanisms, and clinical applications of these next-generation peptide therapeutics.',
                'featured_image': 'https://images.unsplash.com/photo-1576091160550-2173dba999ef?w=800&h=400&fit=crop',
                'author_id': admin_user_id,
                'status': 'published',
                'meta_title': 'Semaglutide vs Retatrutide Comparison | Propeptides',
                'meta_description': 'Detailed comparison of semaglutide and retatrutide, covering efficacy, safety, mechanisms, and clinical applications for metabolic disorders.'
            }
        ]

        # Insert blog posts
        for post_data in blog_posts:
            try:
                cursor.execute("""
                    INSERT INTO post
                    (title, slug, content, excerpt, featured_image, author_id, status, meta_title, meta_description, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    post_data['title'],
                    post_data['slug'],
                    post_data['content'],
                    post_data['excerpt'],
                    post_data['featured_image'],
                    post_data['author_id'],
                    post_data['status'],
                    post_data['meta_title'],
                    post_data['meta_description'],
                    datetime.now(),
                    datetime.now()
                ))
                print(f"✅ Created blog post: {post_data['title']}")
            except pymysql.IntegrityError as e:
                if "Duplicate entry" in str(e):
                    print(f"ℹ️  Blog post already exists: {post_data['title']}")
                else:
                    print(f"❌ Error creating post '{post_data['title']}': {e}")

        # Commit changes
        conn.commit()
        print("\n🎉 Blog posts creation completed!")

        # Display summary
        cursor.execute("SELECT COUNT(*) as total FROM post WHERE status = 'published'")
        result = cursor.fetchone()
        total_posts = result['total']
        print(f"📊 Total published posts in database: {total_posts}")

        # Show latest posts
        cursor.execute("SELECT title, slug, created_at FROM post ORDER BY created_at DESC LIMIT 5")
        latest_posts = cursor.fetchall()
        print("\n📝 Latest posts:")
        for post in latest_posts:
            print(f"  • {post['title']}")
            print(f"    Slug: {post['slug']}")
            print(f"    Created: {post['created_at']}")
            print()

    except Exception as e:
        print(f"❌ Error creating blog posts: {e}")
        if 'conn' in locals():
            conn.rollback()
    finally:
        if 'conn' in locals():
            conn.close()
            print("🔌 Database connection closed.")

if __name__ == "__main__":
    print("🚀 Starting blog posts creation...")
    create_blog_posts()