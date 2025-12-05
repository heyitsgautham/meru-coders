import { ArrowRight, BookOpen, Sparkles, Database, Zap } from "lucide-react";

interface LandingPageProps {
  onLaunchApp: () => void;
}

export function LandingPage({ onLaunchApp }: LandingPageProps) {
  return (
    <div style={{ 
      minHeight: '100vh', 
      backgroundColor: '#faf7f2',
      fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif"
    }}>
      {/* Navigation Bar */}
      <nav style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        height: '70px',
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        backdropFilter: 'blur(10px)',
        borderBottom: '1px solid #e8e0d5',
        zIndex: 1000,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}>
        <div style={{
          width: '100%',
          maxWidth: '1200px',
          padding: '0 60px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <span style={{ 
            fontSize: '24px', 
            fontWeight: 700, 
            color: '#4a2c10',
            letterSpacing: '-0.5px'
          }}>
            Meru Coders
          </span>
          
          <button 
            onClick={onLaunchApp}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '12px 28px',
              backgroundColor: '#c75b1a',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              fontSize: '15px',
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'all 0.2s ease'
            }}
            onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#b34d12'}
            onMouseOut={(e) => e.currentTarget.style.backgroundColor = '#c75b1a'}
          >
            Launch Application
            <ArrowRight size={18} />
          </button>
        </div>
      </nav>

      {/* Hero Section */}
      <section style={{
        paddingTop: '160px',
        paddingBottom: '100px',
        paddingLeft: '60px',
        paddingRight: '60px',
        display: 'flex',
        justifyContent: 'center'
      }}>
        <div style={{
          width: '100%',
          maxWidth: '1200px',
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: '80px',
          alignItems: 'center'
        }}>
          {/* Left Column - Text */}
          <div>
            <div style={{
              display: 'inline-block',
              padding: '8px 16px',
              backgroundColor: '#fff3e6',
              borderRadius: '20px',
              marginBottom: '24px'
            }}>
              <span style={{ 
                fontSize: '13px', 
                fontWeight: 600, 
                color: '#c75b1a',
                letterSpacing: '0.5px'
              }}>
                SANSKRIT PROSODY TOOL
              </span>
            </div>
            
            <h1 style={{
              fontSize: '52px',
              fontWeight: 700,
              color: '#1a1a1a',
              lineHeight: 1.15,
              marginBottom: '24px',
              letterSpacing: '-1px'
            }}>
              Identify Sanskrit{' '}
              <span style={{ color: '#c75b1a' }}>Meters</span>{' '}
              Instantly
            </h1>
            
            <p style={{
              fontSize: '18px',
              color: '#5a5a5a',
              lineHeight: 1.7,
              marginBottom: '40px',
              maxWidth: '480px'
            }}>
              A powerful tool for identifying the <em>chandas</em> (metrical patterns) 
              of Sanskrit verses. Built on Pingala's ancient prosodic system with 
              a database of over 1,900 meters.
            </p>
            
            <div style={{ display: 'flex', gap: '16px' }}>
              <button 
                onClick={onLaunchApp}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px',
                  padding: '16px 32px',
                  backgroundColor: '#c75b1a',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  fontSize: '16px',
                  fontWeight: 600,
                  cursor: 'pointer',
                  transition: 'all 0.2s ease'
                }}
                onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#b34d12'}
                onMouseOut={(e) => e.currentTarget.style.backgroundColor = '#c75b1a'}
              >
                Get Started
                <ArrowRight size={20} />
              </button>
              
              <a 
                href="#what-is-chandas"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  padding: '16px 32px',
                  backgroundColor: 'transparent',
                  color: '#4a2c10',
                  border: '2px solid #d4c4b0',
                  borderRadius: '8px',
                  fontSize: '16px',
                  fontWeight: 600,
                  cursor: 'pointer',
                  textDecoration: 'none',
                  transition: 'all 0.2s ease'
                }}
              >
                Learn More
              </a>
            </div>
          </div>
          
          {/* Right Column - Sample Card */}
          <div style={{
            backgroundColor: 'white',
            borderRadius: '16px',
            padding: '40px',
            boxShadow: '0 4px 40px rgba(0, 0, 0, 0.08)',
            border: '1px solid #e8e0d5'
          }}>
            <div style={{
              fontSize: '13px',
              fontWeight: 600,
              color: '#888',
              marginBottom: '16px',
              letterSpacing: '1px'
            }}>
              SAMPLE INPUT
            </div>
            
            <div style={{
              backgroundColor: '#fffbf5',
              padding: '20px',
              borderRadius: '12px',
              marginBottom: '24px',
              border: '1px solid #e8e0d5'
            }}>
              <p style={{
                fontSize: '22px',
                color: '#4a2c10',
                fontFamily: "'Noto Sans Devanagari', sans-serif",
                lineHeight: 1.6,
                margin: 0
              }}>
                धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः<br />
                मामकाः पाण्डवाश्चैव किमकुर्वत सञ्जय
              </p>
            </div>
            
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              marginBottom: '20px'
            }}>
              <div style={{
                width: '32px',
                height: '32px',
                borderRadius: '50%',
                backgroundColor: '#d4edda',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#28a745" strokeWidth="3">
                  <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
              </div>
              <span style={{ 
                fontSize: '20px', 
                fontWeight: 700, 
                color: '#1a1a1a' 
              }}>
                अनुष्टुभ् (Anuṣṭubh)
              </span>
            </div>
            
            <div style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: '16px'
            }}>
              <div style={{
                backgroundColor: '#f8f9fa',
                padding: '16px',
                borderRadius: '8px'
              }}>
                <div style={{ fontSize: '12px', color: '#888', marginBottom: '4px' }}>
                  Syllables
                </div>
                <div style={{ fontSize: '18px', fontWeight: 600, color: '#1a1a1a' }}>
                  32 (8×4)
                </div>
              </div>
              <div style={{
                backgroundColor: '#f8f9fa',
                padding: '16px',
                borderRadius: '8px'
              }}>
                <div style={{ fontSize: '12px', color: '#888', marginBottom: '4px' }}>
                  Confidence
                </div>
                <div style={{ fontSize: '18px', fontWeight: 600, color: '#28a745' }}>
                  High
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* What is Chandas Section */}
      <section id="what-is-chandas" style={{
        padding: '100px 60px',
        backgroundColor: 'white',
        display: 'flex',
        justifyContent: 'center'
      }}>
        <div style={{
          width: '100%',
          maxWidth: '1200px'
        }}>
          <div style={{
            textAlign: 'center',
            marginBottom: '60px'
          }}>
            <h2 style={{
              fontSize: '40px',
              fontWeight: 700,
              color: '#1a1a1a',
              marginBottom: '20px',
              letterSpacing: '-0.5px'
            }}>
              What is Chandas?
            </h2>
            <p style={{
              fontSize: '18px',
              color: '#5a5a5a',
              maxWidth: '700px',
              margin: '0 auto',
              lineHeight: 1.7
            }}>
              Understanding the ancient science of Sanskrit prosody
            </p>
          </div>
          
          <div style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: '60px',
            alignItems: 'start'
          }}>
            {/* Left - Explanation */}
            <div>
              <div style={{
                backgroundColor: '#fff8f0',
                borderLeft: '4px solid #c75b1a',
                padding: '24px 28px',
                marginBottom: '32px',
                borderRadius: '0 12px 12px 0'
              }}>
                <p style={{
                  fontSize: '20px',
                  color: '#4a2c10',
                  fontStyle: 'italic',
                  margin: 0,
                  lineHeight: 1.6,
                  fontFamily: "'Noto Sans Devanagari', sans-serif"
                }}>
                  "छन्दः पादौ तु वेदस्य"
                </p>
                <p style={{
                  fontSize: '14px',
                  color: '#888',
                  marginTop: '12px',
                  marginBottom: 0
                }}>
                  "Chandas is the feet of the Vedas" — Vedāṅga tradition
                </p>
              </div>
              
              <p style={{
                fontSize: '16px',
                color: '#444',
                lineHeight: 1.8,
                marginBottom: '20px'
              }}>
                <strong>Chandas</strong> (छन्दस्) is the ancient Indian science of prosody—the 
                study of poetic meters in Sanskrit literature. It is one of the six Vedāṅgas 
                (auxiliary disciplines of the Vedas) and forms the rhythmic foundation of 
                all Sanskrit poetry.
              </p>
              
              <p style={{
                fontSize: '16px',
                color: '#444',
                lineHeight: 1.8,
                marginBottom: '20px'
              }}>
                The foundational text is <strong>Pingala's Chandaḥśāstra</strong> (c. 300-200 BCE), 
                which systematically classified meters and introduced concepts that predate 
                Western discoveries by centuries—including binary numbers and what we now 
                call Pascal's Triangle (known in India as <strong>Meru Prastāra</strong>).
              </p>
              
              <p style={{
                fontSize: '16px',
                color: '#444',
                lineHeight: 1.8
              }}>
                Every Sanskrit verse follows a specific metrical pattern determined by the 
                arrangement of <strong>laghu</strong> (light/short) and <strong>guru</strong> (heavy/long) 
                syllables. Identifying these patterns is essential for proper pronunciation, 
                recitation, and understanding of Sanskrit texts.
              </p>
            </div>
            
            {/* Right - Key Concepts */}
            <div>
              <h3 style={{
                fontSize: '22px',
                fontWeight: 700,
                color: '#1a1a1a',
                marginBottom: '28px'
              }}>
                Key Concepts
              </h3>
              
              <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                {/* Laghu */}
                <div style={{
                  backgroundColor: '#faf7f2',
                  padding: '24px',
                  borderRadius: '12px',
                  border: '1px solid #e8e0d5'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '12px' }}>
                    <div style={{
                      width: '48px',
                      height: '48px',
                      borderRadius: '10px',
                      backgroundColor: '#e8f4fd',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '24px',
                      fontWeight: 700,
                      color: '#2196f3'
                    }}>
                      L
                    </div>
                    <div>
                      <div style={{ fontSize: '18px', fontWeight: 600, color: '#1a1a1a' }}>
                        Laghu (लघु)
                      </div>
                      <div style={{ fontSize: '14px', color: '#888' }}>Light / Short syllable</div>
                    </div>
                  </div>
                  <p style={{ fontSize: '14px', color: '#555', margin: 0, lineHeight: 1.6 }}>
                    A syllable with a short vowel (अ, इ, उ, ऋ, ऌ) not followed by a conjunct 
                    consonant or anusvāra/visarga. Counts as 1 mātrā (beat).
                  </p>
                </div>
                
                {/* Guru */}
                <div style={{
                  backgroundColor: '#faf7f2',
                  padding: '24px',
                  borderRadius: '12px',
                  border: '1px solid #e8e0d5'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '12px' }}>
                    <div style={{
                      width: '48px',
                      height: '48px',
                      borderRadius: '10px',
                      backgroundColor: '#fff3e6',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '24px',
                      fontWeight: 700,
                      color: '#c75b1a'
                    }}>
                      G
                    </div>
                    <div>
                      <div style={{ fontSize: '18px', fontWeight: 600, color: '#1a1a1a' }}>
                        Guru (गुरु)
                      </div>
                      <div style={{ fontSize: '14px', color: '#888' }}>Heavy / Long syllable</div>
                    </div>
                  </div>
                  <p style={{ fontSize: '14px', color: '#555', margin: 0, lineHeight: 1.6 }}>
                    A syllable with a long vowel (आ, ई, ऊ, ए, ऐ, ओ, औ) or a short vowel followed 
                    by a conjunct consonant, anusvāra, or visarga. Counts as 2 mātrās.
                  </p>
                </div>
                
                {/* Pada */}
                <div style={{
                  backgroundColor: '#faf7f2',
                  padding: '24px',
                  borderRadius: '12px',
                  border: '1px solid #e8e0d5'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '12px' }}>
                    <div style={{
                      width: '48px',
                      height: '48px',
                      borderRadius: '10px',
                      backgroundColor: '#e8f5e9',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '20px',
                      fontWeight: 700,
                      color: '#4caf50'
                    }}>
                      पद
                    </div>
                    <div>
                      <div style={{ fontSize: '18px', fontWeight: 600, color: '#1a1a1a' }}>
                        Pada (पाद)
                      </div>
                      <div style={{ fontSize: '14px', color: '#888' }}>Quarter / Foot of verse</div>
                    </div>
                  </div>
                  <p style={{ fontSize: '14px', color: '#555', margin: 0, lineHeight: 1.6 }}>
                    A verse is typically divided into 4 padas (quarters). The L-G pattern of 
                    each pada determines the meter. Sama meters have identical padas; 
                    Vishama meters have varying patterns.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section style={{
        padding: '100px 60px',
        backgroundColor: '#faf7f2',
        display: 'flex',
        justifyContent: 'center'
      }}>
        <div style={{
          width: '100%',
          maxWidth: '1200px'
        }}>
          <div style={{
            textAlign: 'center',
            marginBottom: '60px'
          }}>
            <h2 style={{
              fontSize: '40px',
              fontWeight: 700,
              color: '#1a1a1a',
              marginBottom: '20px',
              letterSpacing: '-0.5px'
            }}>
              Features
            </h2>
            <p style={{
              fontSize: '18px',
              color: '#5a5a5a',
              maxWidth: '600px',
              margin: '0 auto',
              lineHeight: 1.7
            }}>
              Everything you need for Sanskrit meter identification
            </p>
          </div>
          
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(4, 1fr)',
            gap: '24px'
          }}>
            {[
              {
                icon: <Database size={28} />,
                title: '1,900+ Meters',
                description: 'Comprehensive database covering Vedic, Classical, Mātrā, and Jāti meters'
              },
              {
                icon: <Zap size={28} />,
                title: 'Instant Analysis',
                description: 'Get meter identification results in milliseconds with confidence scores'
              },
              {
                icon: <BookOpen size={28} />,
                title: 'Multi-Script',
                description: 'Supports Devanagari, IAST, and 10+ Indian regional scripts'
              },
              {
                icon: <Sparkles size={28} />,
                title: 'Smart Matching',
                description: 'Multi-level pattern matching with exact, pada-level, and fuzzy matching'
              }
            ].map((feature, index) => (
              <div key={index} style={{
                backgroundColor: 'white',
                padding: '32px',
                borderRadius: '16px',
                border: '1px solid #e8e0d5',
                textAlign: 'center',
                transition: 'all 0.2s ease'
              }}>
                <div style={{
                  width: '64px',
                  height: '64px',
                  borderRadius: '16px',
                  backgroundColor: '#fff3e6',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  margin: '0 auto 20px',
                  color: '#c75b1a'
                }}>
                  {feature.icon}
                </div>
                <h3 style={{
                  fontSize: '18px',
                  fontWeight: 700,
                  color: '#1a1a1a',
                  marginBottom: '12px'
                }}>
                  {feature.title}
                </h3>
                <p style={{
                  fontSize: '14px',
                  color: '#666',
                  lineHeight: 1.6,
                  margin: 0
                }}>
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Meter Types Section */}
      <section style={{
        padding: '100px 60px',
        backgroundColor: 'white',
        display: 'flex',
        justifyContent: 'center'
      }}>
        <div style={{
          width: '100%',
          maxWidth: '1200px'
        }}>
          <div style={{
            textAlign: 'center',
            marginBottom: '60px'
          }}>
            <h2 style={{
              fontSize: '40px',
              fontWeight: 700,
              color: '#1a1a1a',
              marginBottom: '20px',
              letterSpacing: '-0.5px'
            }}>
              Meter Categories
            </h2>
            <p style={{
              fontSize: '18px',
              color: '#5a5a5a',
              maxWidth: '700px',
              margin: '0 auto',
              lineHeight: 1.7
            }}>
              Our database covers all major categories of Sanskrit meters
            </p>
          </div>
          
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(4, 1fr)',
            gap: '24px'
          }}>
            {[
              { 
                name: 'Vedic Meters', 
                count: 28, 
                description: 'Ancient meters from the Vedas including Gāyatrī, Triṣṭubh, and Jagatī',
                color: '#4a90d9'
              },
              { 
                name: 'Sama Meters', 
                count: 1629, 
                description: 'Classical meters with identical patterns in all four padas',
                color: '#c75b1a'
              },
              { 
                name: 'Ardhasama', 
                count: 180, 
                description: 'Half-equal meters with alternating pada patterns',
                color: '#7b68ee'
              },
              { 
                name: 'Mātrā Meters', 
                count: 9, 
                description: 'Meters based on mātrā (beat) count rather than syllable patterns',
                color: '#2e8b57'
              }
            ].map((type, index) => (
              <div key={index} style={{
                backgroundColor: '#faf7f2',
                padding: '32px',
                borderRadius: '16px',
                border: '1px solid #e8e0d5'
              }}>
                <div style={{
                  fontSize: '48px',
                  fontWeight: 700,
                  color: type.color,
                  marginBottom: '8px'
                }}>
                  {type.count}
                </div>
                <h3 style={{
                  fontSize: '18px',
                  fontWeight: 700,
                  color: '#1a1a1a',
                  marginBottom: '12px'
                }}>
                  {type.name}
                </h3>
                <p style={{
                  fontSize: '14px',
                  color: '#666',
                  lineHeight: 1.6,
                  margin: 0
                }}>
                  {type.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section style={{
        padding: '100px 60px',
        backgroundColor: '#4a2c10',
        display: 'flex',
        justifyContent: 'center'
      }}>
        <div style={{
          width: '100%',
          maxWidth: '800px',
          textAlign: 'center'
        }}>
          <h2 style={{
            fontSize: '40px',
            fontWeight: 700,
            color: 'white',
            marginBottom: '20px',
            letterSpacing: '-0.5px'
          }}>
            Ready to Identify Sanskrit Meters?
          </h2>
          <p style={{
            fontSize: '18px',
            color: 'rgba(255, 255, 255, 0.8)',
            marginBottom: '40px',
            lineHeight: 1.7
          }}>
            Start analyzing Sanskrit verses with our comprehensive meter identification tool.
            Free to use, no registration required.
          </p>
          <button 
            onClick={onLaunchApp}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '12px',
              padding: '18px 40px',
              backgroundColor: '#c75b1a',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              fontSize: '18px',
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'all 0.2s ease'
            }}
            onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#d96b2a'}
            onMouseOut={(e) => e.currentTarget.style.backgroundColor = '#c75b1a'}
          >
            Launch Application
            <ArrowRight size={22} />
          </button>
        </div>
      </section>

      {/* Footer */}
      <footer style={{
        padding: '40px 60px',
        backgroundColor: '#3a2210',
        display: 'flex',
        justifyContent: 'center'
      }}>
        <div style={{
          width: '100%',
          maxWidth: '1200px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <span style={{ 
            fontSize: '18px', 
            fontWeight: 600, 
            color: 'white' 
          }}>
            Meru Coders
          </span>
          <span style={{ 
            fontSize: '14px', 
            color: 'rgba(255, 255, 255, 0.6)' 
          }}>
            Sanskrit Meter Identification Tool
          </span>
        </div>
      </footer>
    </div>
  );
}
