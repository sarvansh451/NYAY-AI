import streamlit as st
from dotenv import load_dotenv
from crew import legal_assistant_crew
import requests
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import time
import PyPDF2
import docx
import io
from groq import Groq
import os
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from datetime import datetime

load_dotenv()

st.set_page_config(page_title="NYAY AI", page_icon="⚖️", layout="wide")

# Sidebar navigation
page = st.sidebar.selectbox("Navigate", ["Legal Assistant", "Document Scanner", "Find Legal Help Nearby"])

# ===========================
# PAGE 1: Legal Assistant
# ===========================
if page == "Legal Assistant":
    st.title("⚖️ NYAY AI - Your Personal Legal Assistant")
    st.markdown(
        "Enter a legal problem in plain English. This assistant will help you:\n"
        "- Understand the legal issue\n"
        "- Find applicable IPC sections\n"
        "- Retrieve matching precedent cases\n"
        "- Generate a formal legal document"
    )

    with st.form("legal_form"):
        user_input = st.text_area("📝 Describe your legal issue:", height=250)
        submitted = st.form_submit_button("🔍 Run NYAY AI")

    if submitted:
        if not user_input.strip():
            st.warning("Please enter a legal issue to analyze.")
        else:
            with st.spinner("🔎 Analyzing your case and preparing legal output..."):
                result = legal_assistant_crew.kickoff(inputs={"user_input": user_input})

            st.success("✅ NYAY AI completed the workflow!")

            st.subheader("📄 Final Output")
            st.markdown(result if isinstance(result, str) else str(result))

# ===========================
# PAGE 2: Document Scanner
# ===========================
elif page == "Document Scanner":
    st.title("📄 Legal Document Scanner")
    st.markdown(
        "Upload a legal document for AI-powered risk analysis. "
        "Each line will be analyzed and color-coded based on potential legal risks."
    )
    
    # Instructions
    with st.expander("ℹ️ How it works", expanded=False):
        st.markdown("""
        **Risk Classification:**
        - 🟢 **Safe** - No legal risks detected
        - 🟡 **Moderate Risk** - Needs minor review or clarification
        - 🔴 **High Risk** - Potential legal problem, requires attention
        
        **Supported formats:** PDF, DOCX, TXT
        """)
    
    # File upload
    uploaded_file = st.file_uploader(
        "Upload your legal document",
        type=['pdf', 'docx', 'txt'],
        help="Maximum file size: 200MB"
    )
    
    if uploaded_file is not None:
        # Extract text based on file type
        try:
            file_text = ""
            
            if uploaded_file.type == "application/pdf":
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
                for page in pdf_reader.pages:
                    file_text += page.extract_text() + "\n"
            
            elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                doc = docx.Document(io.BytesIO(uploaded_file.read()))
                for para in doc.paragraphs:
                    file_text += para.text + "\n"
            
            elif uploaded_file.type == "text/plain":
                file_text = uploaded_file.read().decode('utf-8')
            
            if not file_text.strip():
                st.error("❌ Could not extract text from the document. Please try another file.")
            else:
                st.success(f"✅ Document uploaded: **{uploaded_file.name}**")
                
                # Show document preview
                with st.expander("📖 Document Preview", expanded=False):
                    st.text_area("Content", file_text[:2000] + ("..." if len(file_text) > 2000 else ""), height=200)
                
                # Analyze button
                if st.button("🔍 Analyze Document", type="primary", use_container_width=True):
                    with st.spinner("🤖 AI is analyzing your document for legal risks..."):
                        try:
                            # Initialize Groq client
                            client = Groq(api_key=os.getenv("OPENAI_API_KEY"))
                            
                            # Create analysis prompt
                            prompt = f"""You are a legal expert analyzing a document for potential legal risks. 

Analyze the following document line by line and classify each significant line/clause into one of three risk categories:

🟢 SAFE - No legal risks detected, standard language
🟡 MODERATE - Needs review, ambiguous terms, or minor concerns
🔴 HIGH RISK - Serious legal issues, unfavorable terms, or problematic clauses

For each line you classify, provide:
1. The line/clause text (keep it concise, max 100 chars)
2. Risk level (SAFE, MODERATE, or HIGH)
3. Brief explanation (1-2 sentences)

Format your response as a JSON array like this:
[
  {{"line": "clause text", "risk": "SAFE", "explanation": "why"}},
  {{"line": "clause text", "risk": "MODERATE", "explanation": "why"}},
  {{"line": "clause text", "risk": "HIGH", "explanation": "why"}}
]

Only analyze substantive legal clauses. Skip headers, page numbers, and formatting elements.

DOCUMENT TO ANALYZE:
{file_text[:8000]}"""

                            # Call Groq API
                            completion = client.chat.completions.create(
                                model="llama-3.3-70b-versatile",
                                messages=[
                                    {"role": "system", "content": "You are a legal expert who analyzes documents for legal risks. Always respond with valid JSON."},
                                    {"role": "user", "content": prompt}
                                ],
                                temperature=0.3,
                                max_tokens=8000,
                            )
                            
                            response_text = completion.choices[0].message.content
                            
                            # Parse JSON response
                            import json
                            
                            # Extract JSON from response (handle markdown code blocks)
                            if "```json" in response_text:
                                json_text = response_text.split("```json")[1].split("```")[0].strip()
                            elif "```" in response_text:
                                json_text = response_text.split("```")[1].split("```")[0].strip()
                            else:
                                json_text = response_text.strip()
                            
                            analysis_results = json.loads(json_text)
                            
                            # Display results
                            st.success("✅ Analysis complete!")
                            
                            # Summary metrics
                            col1, col2, col3, col4 = st.columns(4)
                            
                            safe_count = sum(1 for r in analysis_results if r['risk'] == 'SAFE')
                            moderate_count = sum(1 for r in analysis_results if r['risk'] == 'MODERATE')
                            high_count = sum(1 for r in analysis_results if r['risk'] == 'HIGH')
                            
                            with col1:
                                st.metric("Total Clauses", len(analysis_results))
                            with col2:
                                st.metric("🟢 Safe", safe_count)
                            with col3:
                                st.metric("🟡 Moderate", moderate_count)
                            with col4:
                                st.metric("🔴 High Risk", high_count)
                            
                            # Risk distribution chart
                            if safe_count + moderate_count + high_count > 0:
                                st.subheader("📊 Risk Distribution")
                                risk_data = {
                                    "Safe": safe_count,
                                    "Moderate Risk": moderate_count,
                                    "High Risk": high_count
                                }
                                st.bar_chart(risk_data)
                            
                            # Detailed analysis
                            st.subheader("📋 Detailed Analysis")
                            
                            # Group by risk level
                            for risk_level, emoji, color in [
                                ("HIGH", "🔴", "#ff4444"),
                                ("MODERATE", "🟡", "#ffaa00"),
                                ("SAFE", "🟢", "#44ff44")
                            ]:
                                filtered = [r for r in analysis_results if r['risk'] == risk_level]
                                
                                if filtered:
                                    with st.expander(f"{emoji} {risk_level} Risk Items ({len(filtered)})", expanded=(risk_level == "HIGH")):
                                        for idx, item in enumerate(filtered, 1):
                                            st.markdown(f"**{idx}. {item['line'][:150]}{'...' if len(item['line']) > 150 else ''}**")
                                            st.info(f"💡 {item['explanation']}")
                                            if idx < len(filtered):
                                                st.divider()
                            
                            # Download report
                            st.subheader("📥 Download Analysis Report")
                            
                            # Generate PDF with color-coded highlights
                            def create_pdf_report(analysis_results, filename, doc_name):
                                """Generate a color-coded PDF report"""
                                buffer = io.BytesIO()
                                doc = SimpleDocTemplate(buffer, pagesize=letter,
                                                      rightMargin=72, leftMargin=72,
                                                      topMargin=72, bottomMargin=18)
                                
                                # Container for the 'Flowable' objects
                                elements = []
                                
                                # Define styles
                                styles = getSampleStyleSheet()
                                title_style = ParagraphStyle(
                                    'CustomTitle',
                                    parent=styles['Heading1'],
                                    fontSize=24,
                                    textColor=colors.HexColor('#1a1a1a'),
                                    spaceAfter=30,
                                    alignment=TA_CENTER
                                )
                                
                                heading_style = ParagraphStyle(
                                    'CustomHeading',
                                    parent=styles['Heading2'],
                                    fontSize=16,
                                    textColor=colors.HexColor('#2c3e50'),
                                    spaceAfter=12,
                                    spaceBefore=12
                                )
                                
                                # Risk level styles with background colors
                                safe_style = ParagraphStyle(
                                    'Safe',
                                    parent=styles['Normal'],
                                    fontSize=10,
                                    leading=14,
                                    backColor=colors.HexColor('#d4edda'),
                                    borderColor=colors.HexColor('#28a745'),
                                    borderWidth=1,
                                    borderPadding=8,
                                    spaceAfter=10
                                )
                                
                                moderate_style = ParagraphStyle(
                                    'Moderate',
                                    parent=styles['Normal'],
                                    fontSize=10,
                                    leading=14,
                                    backColor=colors.HexColor('#fff3cd'),
                                    borderColor=colors.HexColor('#ffc107'),
                                    borderWidth=1,
                                    borderPadding=8,
                                    spaceAfter=10
                                )
                                
                                high_style = ParagraphStyle(
                                    'High',
                                    parent=styles['Normal'],
                                    fontSize=10,
                                    leading=14,
                                    backColor=colors.HexColor('#f8d7da'),
                                    borderColor=colors.HexColor('#dc3545'),
                                    borderWidth=1,
                                    borderPadding=8,
                                    spaceAfter=10
                                )
                                
                                explanation_style = ParagraphStyle(
                                    'Explanation',
                                    parent=styles['Normal'],
                                    fontSize=9,
                                    textColor=colors.HexColor('#555555'),
                                    leftIndent=20,
                                    spaceAfter=15
                                )
                                
                                # Title
                                elements.append(Paragraph("⚖️ NYAY AI", title_style))
                                elements.append(Paragraph("Legal Document Risk Analysis Report", styles['Heading2']))
                                elements.append(Spacer(1, 0.3*inch))
                                
                                # Document info
                                info_data = [
                                    ['Document:', doc_name],
                                    ['Analysis Date:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
                                    ['Total Clauses:', str(len(analysis_results))]
                                ]
                                
                                info_table = Table(info_data, colWidths=[2*inch, 4*inch])
                                info_table.setStyle(TableStyle([
                                    ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
                                    ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                                    ('TOPPADDING', (0, 0), (-1, -1), 8),
                                    ('GRID', (0, 0), (-1, -1), 1, colors.grey)
                                ]))
                                elements.append(info_table)
                                elements.append(Spacer(1, 0.3*inch))
                                
                                # Summary statistics
                                safe_count = sum(1 for r in analysis_results if r['risk'] == 'SAFE')
                                moderate_count = sum(1 for r in analysis_results if r['risk'] == 'MODERATE')
                                high_count = sum(1 for r in analysis_results if r['risk'] == 'HIGH')
                                
                                summary_data = [
                                    ['Risk Level', 'Count', 'Percentage'],
                                    ['🟢 Safe', str(safe_count), f"{safe_count/len(analysis_results)*100:.1f}%"],
                                    ['🟡 Moderate Risk', str(moderate_count), f"{moderate_count/len(analysis_results)*100:.1f}%"],
                                    ['🔴 High Risk', str(high_count), f"{high_count/len(analysis_results)*100:.1f}%"]
                                ]
                                
                                summary_table = Table(summary_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch])
                                summary_table.setStyle(TableStyle([
                                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
                                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                                    ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#d4edda')),
                                    ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#fff3cd')),
                                    ('BACKGROUND', (0, 3), (-1, 3), colors.HexColor('#f8d7da')),
                                    ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                                    ('FONTSIZE', (0, 1), (-1, -1), 10),
                                    ('TOPPADDING', (0, 1), (-1, -1), 8),
                                    ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
                                ]))
                                elements.append(summary_table)
                                elements.append(Spacer(1, 0.4*inch))
                                
                                # Detailed findings
                                elements.append(Paragraph("DETAILED FINDINGS", heading_style))
                                elements.append(Spacer(1, 0.2*inch))
                                
                                # Group by risk level and display
                                for risk_level, risk_name, style_to_use in [
                                    ("HIGH", "🔴 HIGH RISK ITEMS", high_style),
                                    ("MODERATE", "🟡 MODERATE RISK ITEMS", moderate_style),
                                    ("SAFE", "🟢 SAFE ITEMS", safe_style)
                                ]:
                                    filtered = [r for r in analysis_results if r['risk'] == risk_level]
                                    
                                    if filtered:
                                        elements.append(Paragraph(f"{risk_name} ({len(filtered)})", heading_style))
                                        elements.append(Spacer(1, 0.1*inch))
                                        
                                        for idx, item in enumerate(filtered, 1):
                                            # Clause text with background color
                                            clause_text = f"<b>{idx}.</b> {item['line']}"
                                            elements.append(Paragraph(clause_text, style_to_use))
                                            
                                            # Explanation
                                            explanation_text = f"<i>💡 Analysis:</i> {item['explanation']}"
                                            elements.append(Paragraph(explanation_text, explanation_style))
                                        
                                        elements.append(Spacer(1, 0.2*inch))
                                
                                # Build PDF
                                doc.build(elements)
                                buffer.seek(0)
                                return buffer
                            
                            # Create PDF
                            pdf_buffer = create_pdf_report(analysis_results, uploaded_file.name, uploaded_file.name)
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.download_button(
                                    label="📄 Download Color-Coded PDF Report",
                                    data=pdf_buffer,
                                    file_name=f"legal_analysis_{uploaded_file.name.split('.')[0]}_{int(time.time())}.pdf",
                                    mime="application/pdf",
                                    use_container_width=True
                                )
                            
                            with col2:
                                # Also provide text version
                                report_text = f"""NYAY AI - Legal Document Risk Analysis Report
Document: {uploaded_file.name}
Analysis Date: {time.strftime('%Y-%m-%d %H:%M:%S')}

SUMMARY
========
Total Clauses Analyzed: {len(analysis_results)}
Safe: {safe_count}
Moderate Risk: {moderate_count}
High Risk: {high_count}

DETAILED FINDINGS
=================

"""
                                for risk_level in ["HIGH", "MODERATE", "SAFE"]:
                                    filtered = [r for r in analysis_results if r['risk'] == risk_level]
                                    if filtered:
                                        report_text += f"\n{risk_level} RISK ITEMS ({len(filtered)})\n{'-' * 50}\n\n"
                                        for idx, item in enumerate(filtered, 1):
                                            report_text += f"{idx}. {item['line']}\n"
                                            report_text += f"   Analysis: {item['explanation']}\n\n"
                                
                                st.download_button(
                                    label="📝 Download Text Report",
                                    data=report_text,
                                    file_name=f"legal_analysis_{uploaded_file.name.split('.')[0]}_{int(time.time())}.txt",
                                    mime="text/plain",
                                    use_container_width=True
                                )
                            
                        except json.JSONDecodeError as e:
                            st.error("❌ Error parsing AI response. Please try again.")
                            with st.expander("Debug: View AI Response"):
                                st.code(response_text)
                        except Exception as e:
                            st.error(f"❌ Analysis error: {str(e)}")
                            st.info("💡 Make sure your OPENAI_API_KEY (Groq) is set correctly in your .env file")
        
        except Exception as e:
            st.error(f"❌ Error reading file: {str(e)}")
            st.info("💡 Please ensure the file is not corrupted and try again.")

# ===========================
# PAGE 3: Find Legal Help Nearby
# ===========================
elif page == "Find Legal Help Nearby":
    st.title("📍 Find Legal Help Nearby")
    st.markdown("Discover lawyers, legal aid centers, police stations, and courts near your location.")
    
    # Location input section
    st.subheader("🌍 Enter Your Location")
    col1, col2 = st.columns([3, 1])
    with col1:
        location_input = st.text_input(
            "Location", 
            placeholder="e.g., Bhubaneswar, Odisha or 751001",
            label_visibility="collapsed"
        )
    with col2:
        search_radius = st.selectbox("Radius (km)", [2, 5, 10, 15, 20], index=1)
    
    search_button = st.button("🔍 Search Legal Services", type="primary", use_container_width=True)
    
    if search_button:
        if not location_input:
            st.warning("⚠️ Please enter a location to search.")
        else:
            # Initialize session state for results
            if 'search_results' not in st.session_state:
                st.session_state.search_results = None
            
            with st.spinner("🔎 Locating and searching for nearby legal services..."):
                try:
                    # Initialize geocoder
                    geolocator = Nominatim(user_agent="nyay_ai_legal_v3", timeout=10)
                    
                    # Geocode the location
                    location = geolocator.geocode(location_input, country_codes='in')
                    
                    if not location:
                        st.error("❌ Could not find the location. Please try with:\n- Full address\n- City name\n- Pincode")
                    else:
                        user_lat, user_lon = location.latitude, location.longitude
                        st.success(f"✅ Location found: **{location.address}**")
                        
                        # Function to query Overpass API with better error handling
                        def query_overpass(lat, lon, radius_km, tags, max_retries=2):
                            """Query OpenStreetMap Overpass API with retry logic"""
                            overpass_url = "https://overpass-api.de/api/interpreter"
                            radius_m = radius_km * 1000
                            
                            # Simplified query for faster response
                            tag_queries = []
                            for tag in tags:
                                tag_queries.append(f'node[{tag}](around:{radius_m},{lat},{lon});')
                                tag_queries.append(f'way[{tag}](around:{radius_m},{lat},{lon});')
                            
                            query = f"""
                            [out:json][timeout:15];
                            (
                              {' '.join(tag_queries)}
                            );
                            out body center 100;
                            """
                            
                            for attempt in range(max_retries):
                                try:
                                    response = requests.post(
                                        overpass_url, 
                                        data={'data': query}, 
                                        timeout=20
                                    )
                                    if response.status_code == 200:
                                        return response.json()
                                    elif response.status_code == 429:
                                        time.sleep(2)  # Rate limited, wait and retry
                                        continue
                                    else:
                                        return {'elements': []}
                                except requests.exceptions.Timeout:
                                    if attempt < max_retries - 1:
                                        time.sleep(1)
                                        continue
                                    return {'elements': []}
                                except Exception:
                                    return {'elements': []}
                            
                            return {'elements': []}
                        
                        # Define search categories
                        search_categories = {
                            "👨‍⚖️ Lawyers": {
                                "tags": ['office=lawyer'],
                                "icon": ("blue", "briefcase"),
                            },
                            "🤝 Legal Aid": {
                                "tags": ['office=ngo', 'amenity=social_facility'],
                                "icon": ("green", "hands-helping"),
                            },
                            "🚔 Police": {
                                "tags": ['amenity=police'],
                                "icon": ("darkblue", "shield-alt"),
                            },
                            "🏛️ Courts": {
                                "tags": ['amenity=courthouse'],
                                "icon": ("purple", "landmark"),
                            }
                        }
                        
                        # Store all results
                        all_results = {}
                        total_found = 0
                        
                        # Search each category with progress updates
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        for idx, (category_name, category_info) in enumerate(search_categories.items()):
                            status_text.text(f"Searching for {category_name}...")
                            
                            # Query API
                            data = query_overpass(user_lat, user_lon, search_radius, category_info['tags'])
                            places = []
                            
                            for element in data.get('elements', []):
                                try:
                                    # Get coordinates
                                    if 'lat' in element and 'lon' in element:
                                        place_lat, place_lon = element['lat'], element['lon']
                                    elif 'center' in element:
                                        place_lat, place_lon = element['center']['lat'], element['center']['lon']
                                    else:
                                        continue
                                    
                                    # Get place details
                                    tags = element.get('tags', {})
                                    name = tags.get('name', tags.get('operator', 'Unnamed'))
                                    
                                    # Build address
                                    address_parts = []
                                    for key in ['addr:street', 'addr:city', 'addr:state']:
                                        if key in tags and tags[key]:
                                            address_parts.append(tags[key])
                                    address = ', '.join(address_parts) if address_parts else 'Not available'
                                    
                                    phone = tags.get('phone', tags.get('contact:phone', 'Not available'))
                                    website = tags.get('website', tags.get('contact:website', ''))
                                    
                                    # Calculate distance
                                    distance = geodesic((user_lat, user_lon), (place_lat, place_lon)).km
                                    
                                    if distance <= search_radius:
                                        places.append({
                                            'name': name,
                                            'address': address,
                                            'phone': phone,
                                            'website': website,
                                            'distance': round(distance, 2),
                                            'lat': place_lat,
                                            'lon': place_lon,
                                            'icon': category_info['icon']
                                        })
                                except:
                                    continue
                            
                            # Sort by distance
                            places.sort(key=lambda x: x['distance'])
                            all_results[category_name] = places
                            total_found += len(places)
                            
                            # Update progress
                            progress_bar.progress((idx + 1) / len(search_categories))
                            time.sleep(0.5)  # Prevent rate limiting
                        
                        progress_bar.empty()
                        status_text.empty()
                        
                        # Store results in session state
                        st.session_state.search_results = {
                            'user_lat': user_lat,
                            'user_lon': user_lon,
                            'radius': search_radius,
                            'location_name': location.address,
                            'all_results': all_results,
                            'total_found': total_found
                        }
                        
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    st.info("💡 Try again or use a different location.")
    
    # Display results if they exist in session state
    if st.session_state.get('search_results'):
        results = st.session_state.search_results
        user_lat = results['user_lat']
        user_lon = results['user_lon']
        search_radius = results['radius']
        all_results = results['all_results']
        total_found = results['total_found']
        
        st.info(f"🔍 Found **{total_found}** legal services within **{search_radius} km**")
        
        # Create map (stable version)
        try:
            map_center = [user_lat, user_lon]
            m = folium.Map(
                location=map_center, 
                zoom_start=13, 
                tiles='OpenStreetMap',
                prefer_canvas=True
            )
            
            # Add user location
            folium.Marker(
                map_center,
                popup="<b>Your Location</b>",
                tooltip="You are here",
                icon=folium.Icon(color='red', icon='home', prefix='fa')
            ).add_to(m)
            
            # Add radius circle
            folium.Circle(
                map_center,
                radius=search_radius * 1000,
                color='red',
                fill=True,
                fillOpacity=0.08,
                weight=2
            ).add_to(m)
            
            # Add markers for all places
            marker_count = 0
            for category_name, places in all_results.items():
                for place in places[:20]:  # Limit markers to prevent crash
                    try:
                        color, icon_name = place['icon']
                        
                        popup_html = f"""
                        <b>{place['name']}</b><br>
                        Distance: {place['distance']} km<br>
                        {place['address']}<br>
                        Phone: {place['phone']}
                        """
                        
                        folium.Marker(
                            [place['lat'], place['lon']],
                            popup=folium.Popup(popup_html, max_width=250),
                            tooltip=f"{place['name']}",
                            icon=folium.Icon(color=color, icon=icon_name, prefix='fa')
                        ).add_to(m)
                        
                        marker_count += 1
                    except:
                        continue
            
            # Display map
            st.subheader("🗺️ Interactive Map")
            st.caption(f"Showing {marker_count} locations on map. Click markers for details.")
            
            # Use key to prevent re-rendering issues
            st_folium(
                m, 
                width=700, 
                height=500,
                returned_objects=[],
                key="legal_services_map"
            )
            
        except Exception as e:
            st.warning(f"Map display error. Showing list view only.")
        
        # Display results list
        st.subheader("📋 Nearby Legal Services")
        
        for category_name, places in all_results.items():
            with st.expander(f"{category_name} ({len(places)} found)", expanded=False):
                if places:
                    for idx, place in enumerate(places[:10], 1):
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            st.markdown(f"**{idx}. {place['name']}**")
                            st.caption(f"📍 {place['address']}")
                            if place['phone'] != 'Not available':
                                st.caption(f"📞 {place['phone']}")
                            if place['website']:
                                st.caption(f"🌐 [Website]({place['website']})")
                        
                        with col2:
                            st.metric("Distance", f"{place['distance']} km")
                        
                        if idx < len(places[:10]):
                            st.divider()
                    
                    if len(places) > 10:
                        st.info(f"+ {len(places) - 10} more locations")
                else:
                    st.info(f"No results found. Try increasing search radius.")
        
        # Clear results button
        if st.button("🔄 New Search"):
            st.session_state.search_results = None
            st.rerun()

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("**NYAY AI** - Legal Access")
st.sidebar.caption("Powered by Groq AI & OpenStreetMap")