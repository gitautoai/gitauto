/* eslint-disable @typescript-eslint/no-unused-vars, @typescript-eslint/no-var-requires */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import React from 'react';

import CoverageOption from './CoverageOption';
import { CoverageOptionData } from './CoverageOptionTypes';

describe('CoverageOption', () => {
  const defaultProps = {
    coverageTitle: 'Test Coverage',
    coverageDescription: 'Test Description',
    value: { chooseCoverage: false, coverageLimit: '' },
    onChange: jest.fn()
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Rendering', () => {
    it('renders without crashing', () => {
      render(<CoverageOption {...defaultProps} />);
      expect(screen.getByTestId('CoverageOption')).toBeInTheDocument();
    });

    it('renders coverage title', () => {
      render(<CoverageOption {...defaultProps} />);
      expect(screen.getByText('Test Coverage')).toBeInTheDocument();
    });

    it('renders coverage description', () => {
      render(<CoverageOption {...defaultProps} />);
      expect(screen.getByText('Test Description')).toBeInTheDocument();
    });

    it('renders checkbox', () => {
      render(<CoverageOption {...defaultProps} />);
      const checkbox = screen.getByRole('checkbox');
      expect(checkbox).toBeInTheDocument();
    });

    it('renders help button when helperText is provided', () => {
      render(
        <CoverageOption {...defaultProps} helperText="<p>Help content</p>" />
      );
      const helpButton = screen.getByText('?');
      expect(helpButton).toBeInTheDocument();
    });

    it('does not render help button when helperText is not provided', () => {
      render(<CoverageOption {...defaultProps} />);
      const helpButton = screen.queryByText('?');
      expect(helpButton).not.toBeInTheDocument();
    });
  });

  describe('Checkbox Behavior', () => {
    it('checkbox is unchecked when chooseCoverage is false', () => {
      render(<CoverageOption {...defaultProps} />);
      const checkbox = screen.getByRole('checkbox') as HTMLInputElement;
      expect(checkbox.checked).toBe(false);
    });

    it('checkbox is checked when chooseCoverage is true', () => {
      const props = {
        ...defaultProps,
        value: { chooseCoverage: true, coverageLimit: '' }
      };
      render(<CoverageOption {...props} />);
      const checkbox = screen.getByRole('checkbox') as HTMLInputElement;
      expect(checkbox.checked).toBe(true);
    });

    it('calls onChange when checkbox is clicked', () => {
      const onChange = jest.fn();
      render(<CoverageOption {...defaultProps} onChange={onChange} />);
      const checkbox = screen.getByRole('checkbox');
      fireEvent.click(checkbox);
      expect(onChange).toHaveBeenCalledWith({
        chooseCoverage: true,
        coverageLimit: ''
      });
    });

    it('calls onChange when container is clicked', () => {
      const onChange = jest.fn();
      render(<CoverageOption {...defaultProps} onChange={onChange} />);
      const container = screen.getByTestId('CoverageOption');
      fireEvent.click(container);
      expect(onChange).toHaveBeenCalledWith({
        chooseCoverage: true,
        coverageLimit: ''
      });
    });

    it('toggles chooseCoverage from false to true', () => {
      const onChange = jest.fn();
      render(<CoverageOption {...defaultProps} onChange={onChange} />);
      const container = screen.getByTestId('CoverageOption');
      fireEvent.click(container);
      expect(onChange).toHaveBeenCalledWith({
        chooseCoverage: true,
        coverageLimit: ''
      });
    });

    it('toggles chooseCoverage from true to false', () => {
      const onChange = jest.fn();
      const props = {
        ...defaultProps,
        value: { chooseCoverage: true, coverageLimit: '' },
        onChange
      };
      render(<CoverageOption {...props} />);
      const container = screen.getByTestId('CoverageOption');
      fireEvent.click(container);
      expect(onChange).toHaveBeenCalledWith({
        chooseCoverage: false,
        coverageLimit: ''
      });
    });

    it('preserves coverageLimit when toggling', () => {
      const onChange = jest.fn();
      const props = {
        ...defaultProps,
        value: { chooseCoverage: false, coverageLimit: '100000' },
        onChange
      };
      render(<CoverageOption {...props} />);
      const container = screen.getByTestId('CoverageOption');
      fireEvent.click(container);
      expect(onChange).toHaveBeenCalledWith({
        chooseCoverage: true,
        coverageLimit: '100000'
      });
    });
  });

  describe('Read-Only Mode', () => {
    it('does not call onChange when readOnly is true', () => {
      const onChange = jest.fn();
      render(
        <CoverageOption {...defaultProps} onChange={onChange} readOnly={true} />
      );
      const container = screen.getByTestId('CoverageOption');
      fireEvent.click(container);
      expect(onChange).not.toHaveBeenCalled();
    });

    it('checkbox is disabled when readOnly is true', () => {
      render(<CoverageOption {...defaultProps} readOnly={true} />);
      const checkbox = screen.getByRole('checkbox') as HTMLInputElement;
      expect(checkbox.disabled).toBe(true);
    });

    it('applies correct styling when readOnly is true', () => {
      render(<CoverageOption {...defaultProps} readOnly={true} />);
      const container = screen.getByTestId('CoverageOption');
      expect(container.className).toContain('border-faded');
    });
  });

  describe('Styling', () => {
    it('applies secondary border when coverage is chosen', () => {
      const props = {
        ...defaultProps,
        value: { chooseCoverage: true, coverageLimit: '' }
      };
      render(<CoverageOption {...props} />);
      const container = screen.getByTestId('CoverageOption');
      expect(container.className).toContain('border-secondary');
    });

    it('applies faded border when coverage is not chosen', () => {
      render(<CoverageOption {...defaultProps} />);
      const container = screen.getByTestId('CoverageOption');
      expect(container.className).toContain('border-faded');
    });

    it('applies cursor-pointer class when not readOnly', () => {
      render(<CoverageOption {...defaultProps} />);
      const container = screen.getByTestId('CoverageOption');
      expect(container.className).toContain('cursor-pointer');
    });
  });

  describe('Modal Functionality', () => {
    it('opens modal when help button is clicked', async () => {
      render(
        <CoverageOption {...defaultProps} helperText="<p>Help content</p>" />
      );
      const helpButton = screen.getByText('?');
      fireEvent.click(helpButton);

      await waitFor(() => {
        const modalContent = screen.getByText('Help content');
        expect(modalContent).toBeInTheDocument();
      }, { timeout: 10000 });
    });

    it('does not trigger onChange when help button is clicked', () => {
      const onChange = jest.fn();
      render(
        <CoverageOption
          {...defaultProps}
          onChange={onChange}
          helperText="<p>Help content</p>"
        />
      );
      const helpButton = screen.getByText('?');
      fireEvent.click(helpButton);
      expect(onChange).not.toHaveBeenCalled();
    });

    it('renders helper text content in modal', async () => {
      render(
        <CoverageOption
          {...defaultProps}
          helperText="<p>Custom help text</p>"
        />
      );
      const helpButton = screen.getByText('?');
      fireEvent.click(helpButton);

      await waitFor(() => {
        expect(screen.getByText('Custom help text')).toBeInTheDocument();
      });
    });

    it('closes modal when handleModalClose is called', async () => {
      render(
        <CoverageOption
          {...defaultProps}
          helperText="<p>Help content</p>"
        />
      );
      const helpButton = screen.getByText('?');
      fireEvent.click(helpButton);

      await waitFor(() => {
        expect(screen.getByText('Help content')).toBeInTheDocument();
      });

      const modal = screen.getByRole('presentation');
      fireEvent.click(modal);

      await waitFor(() => {
        expect(screen.queryByText('Help content')).not.toBeInTheDocument();
      });
    });
  });

  describe('Read More and Collapse Text Functionality', () => {
    it('shows description when "Read more.." is clicked', () => {
      render(<CoverageOption {...defaultProps} />);
      const readMoreButton = screen.getByText('Read more..');
      fireEvent.click(readMoreButton);
      const collapseButton = screen.getByText('Collapse Text');
      expect(collapseButton).toBeInTheDocument();
    });

    it('hides description when "Collapse Text" is clicked', () => {
      render(<CoverageOption {...defaultProps} />);
      const readMoreButton = screen.getByText('Read more..');
      fireEvent.click(readMoreButton);
      const collapseButton = screen.getByText('Collapse Text');
      fireEvent.click(collapseButton);
      expect(screen.getByText('Read more..')).toBeInTheDocument();
    });

    it('does not trigger onChange when "Read more.." is clicked', () => {
      const onChange = jest.fn();
      render(<CoverageOption {...defaultProps} onChange={onChange} />);
      const readMoreButton = screen.getByText('Read more..');
      fireEvent.click(readMoreButton);
      expect(onChange).not.toHaveBeenCalled();
    });

    it('does not trigger onChange when "Collapse Text" is clicked', () => {
      const onChange = jest.fn();
      render(<CoverageOption {...defaultProps} onChange={onChange} />);
      const readMoreButton = screen.getByText('Read more..');
      fireEvent.click(readMoreButton);
      const collapseButton = screen.getByText('Collapse Text');
      fireEvent.click(collapseButton);
      expect(onChange).not.toHaveBeenCalled();
    });

    it('toggles description visibility when "Read more.." is clicked', () => {
      render(<CoverageOption {...defaultProps} />);
      const readMoreButton = screen.getByText('Read more..');
      expect(readMoreButton).toBeInTheDocument();
      fireEvent.click(readMoreButton);
      expect(screen.getByText('Collapse Text')).toBeInTheDocument();
    });

    it('toggles description visibility when "Collapse Text" is clicked', () => {
      render(<CoverageOption {...defaultProps} />);
      const readMoreButton = screen.getByText('Read more..');
      fireEvent.click(readMoreButton);
      const collapseButton = screen.getByText('Collapse Text');
      expect(collapseButton).toBeInTheDocument();
      fireEvent.click(collapseButton);
      expect(screen.getByText('Read more..')).toBeInTheDocument();
    });

    it('shows description when showDescription is true', () => {
      render(<CoverageOption {...defaultProps} />);
      const readMoreButton = screen.getByText('Read more..');
      fireEvent.click(readMoreButton);
      const description = screen.getByText('Test Description');
      expect(description).toBeInTheDocument();
    });

    it('hides "Read more.." button when description is shown', () => {
      render(<CoverageOption {...defaultProps} />);
      const readMoreButton = screen.getByText('Read more..');
      fireEvent.click(readMoreButton);
      expect(readMoreButton).toHaveClass('hidden');
    });
  });

  describe('Coverage Limit', () => {
    it('handles empty coverageLimit', () => {
      const onChange = jest.fn();
      const props = {
        ...defaultProps,
        value: { chooseCoverage: false, coverageLimit: '' },
        onChange
      };
      render(<CoverageOption {...props} />);
      const container = screen.getByTestId('CoverageOption');
      fireEvent.click(container);
      expect(onChange).toHaveBeenCalledWith({
        chooseCoverage: true,
        coverageLimit: ''
      });
    });

    it('handles undefined value', () => {
      const onChange = jest.fn();
      const props = {
        ...defaultProps,
        value: undefined as unknown as CoverageOptionData,
        onChange
      };
      render(<CoverageOption {...props} />);
      const container = screen.getByTestId('CoverageOption');
      fireEvent.click(container);
      expect(onChange).toHaveBeenCalledWith({
        chooseCoverage: true,
        coverageLimit: ''
      });
    });
  });

  describe('Show/Hide Description', () => {
    it('renders description when provided', () => {
      render(<CoverageOption {...defaultProps} />);
      expect(screen.getByText('Test Description')).toBeInTheDocument();
    });

    it('does not render description when not provided', () => {
      const props = {
        ...defaultProps,
        coverageDescription: undefined
      };
      render(<CoverageOption {...props} />);
      expect(screen.queryByText('Test Description')).not.toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('handles missing coverageTitle', () => {
      const props = {
        ...defaultProps,
        coverageTitle: undefined
      };
      render(<CoverageOption {...props} />);
      expect(screen.getByTestId('CoverageOption')).toBeInTheDocument();
    });

    it('handles missing coverageDescription', () => {
      const props = {
        ...defaultProps,
        coverageDescription: undefined
      };
      render(<CoverageOption {...props} />);
      expect(screen.getByTestId('CoverageOption')).toBeInTheDocument();
    });

    it('handles null value', () => {
      const onChange = jest.fn();
      const props = {
        ...defaultProps,
        value: null as unknown as CoverageOptionData,
        onChange
      };
      render(<CoverageOption {...props} />);
      const container = screen.getByTestId('CoverageOption');
      fireEvent.click(container);
      expect(onChange).toHaveBeenCalledWith({
        chooseCoverage: true,
        coverageLimit: ''
      });
    }, 30000);
  });

  describe('HTML Parsing', () => {
    it('parses HTML in helperText', async () => {
      render(
        <CoverageOption
          {...defaultProps}
          helperText="<p><strong>Bold text</strong></p>"
        />
      );
      const helpButton = screen.getByText('?');
      fireEvent.click(helpButton);

      await waitFor(() => {
        expect(screen.getByText('Bold text')).toBeInTheDocument();
      });
    });

    it('handles complex HTML in helperText', async () => {
      const complexHtml =
        '<div><h1>Title</h1><p>Paragraph</p><ul><li>Item 1</li></ul></div>';
      render(<CoverageOption {...defaultProps} helperText={complexHtml} />);
      const helpButton = screen.getByText('?');
      fireEvent.click(helpButton);

      await waitFor(() => {
        expect(screen.getByText('Title')).toBeInTheDocument();
        expect(screen.getByText('Paragraph')).toBeInTheDocument();
        expect(screen.getByText('Item 1')).toBeInTheDocument();
      });
    }, 30000);
  });

  describe('Multiple Instances', () => {
    it('handles multiple instances independently', () => {
      const onChange1 = jest.fn();
      const onChange2 = jest.fn();

      render(
        <div>
          <CoverageOption
            {...defaultProps}
            coverageTitle="Coverage 1"
            onChange={onChange1}
          />
          <CoverageOption
            {...defaultProps}
            coverageTitle="Coverage 2"
            onChange={onChange2}
          />
        </div>
      );

      const containers = screen.getAllByTestId('CoverageOption');
      fireEvent.click(containers[0]);
      expect(onChange1).toHaveBeenCalled();
      expect(onChange2).not.toHaveBeenCalled();
    });
  });

  describe('Checkbox State Consistency', () => {
    it('checkbox state matches value prop', () => {
      const { rerender } = render(<CoverageOption {...defaultProps} />);
      let checkbox = screen.getByRole('checkbox') as HTMLInputElement;
      expect(checkbox.checked).toBe(false);

      rerender(
        <CoverageOption
          {...defaultProps}
          value={{ chooseCoverage: true, coverageLimit: '' }}
        />
      );
      checkbox = screen.getByRole('checkbox') as HTMLInputElement;
      expect(checkbox.checked).toBe(true);
    });
  });

  describe('Accessibility', () => {
    it('checkbox has aria-label', () => {
      render(<CoverageOption {...defaultProps} />);
      const checkbox = screen.getByRole('checkbox');
      expect(checkbox).toHaveAttribute('aria-label', 'primary checkbox');
    });

    it('checkbox is accessible via keyboard', () => {
      render(<CoverageOption {...defaultProps} />);
      const checkbox = screen.getByRole('checkbox');
      checkbox.focus();
      expect(checkbox).toHaveFocus();
    });
  });
});
